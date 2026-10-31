package com.chhatralekha.core.network

import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpHandler
import com.sun.net.httpserver.HttpServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.net.InetSocketAddress
import java.nio.charset.StandardCharsets

/**
 * Real integration test testing ChhatraLekhaApiClient and SyncManager over real TCP HTTP requests
 * using an in-process local HTTP server on an ephemeral port.
 */
class ChhatraLekhaApiClientTest {

    private lateinit var server: HttpServer
    private var baseUrl: String = ""
    private val client = ChhatraLekhaApiClient(connectTimeoutMs = 2000, readTimeoutMs = 2000)

    @Before
    fun setUp() {
        server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)

        // Health endpoint
        server.createContext("/health", HttpHandler { exchange ->
            respondJson(exchange, 200, "{\"status\":\"ok\",\"service\":\"chhatralekha\"}")
        })

        // Token verification endpoint
        server.createContext("/api/verify/token/", HttpHandler { exchange ->
            val path = exchange.requestURI.path
            val token = path.substringAfter("/api/verify/token/")
            when (token) {
                "tok_valid_123" -> {
                    respondJson(
                        exchange,
                        200,
                        """
                        {
                            "valid": true,
                            "verdict": "VALID",
                            "reason": "Cryptographically verified credential",
                            "institution": "IIT Bombay",
                            "programme": "BTECH_CSE",
                            "academic_year": "2024-25",
                            "record_status": "ACTIVE",
                            "issued_at": 1726000000,
                            "expires_at": 1757536000
                        }
                        """.trimIndent()
                    )
                }
                "tok_revoked_456" -> {
                    respondJson(
                        exchange,
                        200,
                        """
                        {
                            "valid": false,
                            "verdict": "REVOKED",
                            "reason": "This verification token was revoked by the institution",
                            "institution": "IIT Delhi"
                        }
                        """.trimIndent()
                    )
                }
                else -> {
                    respondJson(exchange, 404, "{\"detail\":\"No such verification token.\"}")
                }
            }
        })

        // Students endpoint (GET & POST)
        server.createContext("/api/students", HttpHandler { exchange ->
            when (exchange.requestMethod.uppercase()) {
                "GET" -> {
                    val json = """
                        [
                            {
                                "record_id": "rec_001",
                                "apaar_id": "984210357890",
                                "student_name": "BAISHNABI DAS",
                                "date_of_birth": "2003-05-14",
                                "gender": "F",
                                "institution_id": "INST-0421",
                                "program_id": "BTECH_CSE",
                                "academic_year": "2024-25",
                                "admission_quota": "MERIT",
                                "enrollment_date": "2024-08-01",
                                "student_institute_roll_no": "CSE-24-001",
                                "nationality": "Indian",
                                "verification_status": "VERIFIED"
                            }
                        ]
                    """.trimIndent()
                    respondJson(exchange, 200, json)
                }
                "POST" -> {
                    val path = exchange.requestURI.path
                    if (path.endsWith("/token")) {
                        respondJson(
                            exchange,
                            200,
                            "{\"token\":\"tok_test_984210357890\",\"token_url\":\"https://chhatralekha.vercel.app/verify/t/tok_test_984210357890\"}"
                        )
                        return@HttpHandler
                    }
                    val body = exchange.requestBody.bufferedReader(StandardCharsets.UTF_8).readText()
                    if (body.contains("999999999999")) {
                        // Simulate duplicate conflict
                        respondJson(exchange, 409, "{\"detail\":\"Duplicate APAAR ID across institutions\"}")
                    } else {
                        respondJson(exchange, 201, "{\"record_id\":\"rec_new_999\",\"status\":\"created\"}")
                    }
                }
                else -> {
                    exchange.sendResponseHeaders(405, -1)
                }
            }
        })

        server.start()
        baseUrl = "http://127.0.0.1:${server.address.port}/api"
    }

    @After
    fun tearDown() {
        server.stop(0)
    }

    private fun respondJson(exchange: HttpExchange, statusCode: Int, json: String) {
        val bytes = json.toByteArray(StandardCharsets.UTF_8)
        exchange.responseHeaders.set("Content-Type", "application/json")
        exchange.sendResponseHeaders(statusCode, bytes.size.toLong())
        exchange.responseBody.use { it.write(bytes) }
    }

    @Test
    fun testCheckHealthSuccessful() {
        val result = client.checkHealth(baseUrl)
        assertTrue("Health check should succeed", result is NetworkResult.Success)
        assertEquals(true, (result as NetworkResult.Success).data)
    }

    @Test
    fun testVerifyValidTokenReturnsVerifiedDetails() {
        val result = client.verifyToken("tok_valid_123", baseUrl)
        assertTrue(result is NetworkResult.Success)
        val data = (result as NetworkResult.Success).data
        assertTrue(data.valid)
        assertEquals("VALID", data.verdict)
        assertEquals("IIT Bombay", data.institution)
        assertEquals("BTECH_CSE", data.programme)
        assertEquals("2024-25", data.academicYear)
    }

    @Test
    fun testVerifyRevokedTokenReturnsRevokedVerdict() {
        val result = client.verifyToken("tok_revoked_456", baseUrl)
        assertTrue(result is NetworkResult.Success)
        val data = (result as NetworkResult.Success).data
        assertFalse(data.valid)
        assertEquals("REVOKED", data.verdict)
    }

    @Test
    fun testVerifyNonExistentTokenReturnsNotFound() {
        val result = client.verifyToken("tok_does_not_exist", baseUrl)
        assertTrue(result is NetworkResult.Success)
        val data = (result as NetworkResult.Success).data
        assertFalse(data.valid)
        assertEquals("NOT_FOUND", data.verdict)
    }

    @Test
    fun testRequestVerificationTokenReturnsOpaqueToken() {
        val result = client.requestVerificationToken("984210357890", baseUrl = baseUrl)
        assertTrue(result is NetworkResult.Success)
        val token = (result as NetworkResult.Success).data
        assertEquals("tok_test_984210357890", token)
    }

    @Test
    fun testFetchStudentsReturnsList() {
        val result = client.fetchStudents(baseUrl = baseUrl)
        assertTrue(result is NetworkResult.Success)
        val list = (result as NetworkResult.Success).data
        assertEquals(1, list.size)
        assertEquals("984210357890", list[0].apaarId)
        assertEquals("BAISHNABI DAS", list[0].studentName)
    }

    @Test
    fun testSubmitStudentSuccessAndConflictHandling() {
        val validStudent = RemoteStudentDto(
            apaarId = "123456789012",
            studentName = "Rahul Sharma",
            dateOfBirth = "2002-11-10",
            gender = "M",
            institutionId = "INST-0421",
            programId = "BTECH_ECE",
            academicYear = "2024-25",
            enrollmentDate = "2024-08-01"
        )
        val successRes = client.submitStudent(validStudent, baseUrl = baseUrl)
        assertTrue(successRes is NetworkResult.Success)
        assertEquals("rec_new_999", (successRes as NetworkResult.Success).data.recordId)

        val duplicateStudent = validStudent.copy(apaarId = "999999999999")
        val conflictRes = client.submitStudent(duplicateStudent, baseUrl = baseUrl)
        assertTrue(conflictRes is NetworkResult.Error)
        assertEquals(409, (conflictRes as NetworkResult.Error).statusCode)
    }

    @Test
    fun testOfflineFallbackWhenServerUnreachable() {
        // Point to an unopened port on loopback
        val offlineUrl = "http://127.0.0.1:65432/api"
        val result = client.verifyToken("tok_test", offlineUrl)
        assertTrue("Should fallback to offline when server unreachable", result is NetworkResult.OfflineFallback)
        assertNotNull((result as NetworkResult.OfflineFallback).reason)
    }

    @Test
    fun testSyncManagerPerformsSyncWithSafeConflictHandling() {
        val syncManager = SyncManager(client)
        val localRecords = listOf(
            RemoteStudentDto(
                apaarId = "111122223333",
                studentName = "Local Student 1",
                dateOfBirth = "2003-01-01",
                gender = "F",
                institutionId = "INST-0421",
                programId = "BTECH_CSE",
                academicYear = "2024-25",
                enrollmentDate = "2024-08-01"
            ),
            RemoteStudentDto(
                apaarId = "999999999999", // will trigger 409 conflict
                studentName = "Duplicate Student",
                dateOfBirth = "2003-01-01",
                gender = "M",
                institutionId = "INST-0421",
                programId = "BTECH_CSE",
                academicYear = "2024-25",
                enrollmentDate = "2024-08-01"
            )
        )

        val summary = syncManager.performSync(baseUrl, localStudents = localRecords)
        assertFalse(summary.isOffline)
        assertEquals(1, summary.pushedCount)
        assertEquals(1, summary.conflictsCount)
        assertEquals(1, summary.pulledCount)
    }

    @Test
    fun testSyncManagerGracefullyReportsOfflineWhenServerDown() {
        val syncManager = SyncManager(client)
        val offlineUrl = "http://127.0.0.1:65432/api"
        val summary = syncManager.performSync(offlineUrl, localStudents = emptyList())
        assertTrue(summary.isOffline)
        assertEquals(0, summary.pushedCount)
        assertEquals(0, summary.pulledCount)
    }
}
