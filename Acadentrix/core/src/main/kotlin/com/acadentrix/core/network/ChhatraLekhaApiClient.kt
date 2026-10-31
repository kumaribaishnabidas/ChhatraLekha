package com.acadentrix.core.network

import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets

/**
 * Standard HTTP client connecting the Android application to the ChhatraLekha backend API.
 * Uses zero third-party dependencies, leveraging standard Java runtime networking
 * to ensure deterministic, crash-free execution across all Android API levels.
 */
class ChhatraLekhaApiClient(
    val defaultBaseUrl: String = DEFAULT_BASE_URL,
    private val connectTimeoutMs: Int = 8000,
    private val readTimeoutMs: Int = 12000
) {
    companion object {
        const val DEFAULT_BASE_URL = "http://10.0.2.2:8000/api"
        const val PRODUCTION_API_URL = "https://chhatralekha-api.onrender.com/api"
    }

    /**
     * Checks backend service health.
     */
    fun checkHealth(baseUrl: String = defaultBaseUrl): NetworkResult<Boolean> {
        val rootUrl = baseUrl.removeSuffix("/api").removeSuffix("/")
        val healthUrl = "$rootUrl/health"
        return executeGet(healthUrl) { body, code ->
            if (code in 200..299) {
                NetworkResult.Success(true, code)
            } else {
                NetworkResult.Error(code, "Health check failed with status $code")
            }
        }
    }

    /**
     * Verifies an opaque token via the public endpoint:
     * GET /api/verify/token/{token}
     */
    fun verifyToken(
        token: String,
        baseUrl: String = defaultBaseUrl
    ): NetworkResult<RemoteTokenVerification> {
        if (token.isBlank()) {
            return NetworkResult.Error(400, "Token cannot be blank")
        }
        val cleanBase = baseUrl.trimEnd('/')
        val url = "$cleanBase/verify/token/${encodeUri(token)}"

        return executeGet(url) { body, code ->
            if (code in 200..299) {
                val valid = extractBoolean(body, "valid") ?: false
                val verdict = extractString(body, "verdict") ?: "UNKNOWN"
                val reason = extractString(body, "reason") ?: ""
                val institution = extractString(body, "institution")
                val programme = extractString(body, "programme")
                val academicYear = extractString(body, "academic_year")
                val recordStatus = extractString(body, "record_status")
                val issuedAt = extractLong(body, "issued_at")
                val expiresAt = extractLong(body, "expires_at")
                val notice = extractString(body, "notice")

                NetworkResult.Success(
                    RemoteTokenVerification(
                        valid = valid,
                        verdict = verdict,
                        reason = reason,
                        institution = institution,
                        programme = programme,
                        academicYear = academicYear,
                        recordStatus = recordStatus,
                        issuedAt = issuedAt,
                        expiresAt = expiresAt,
                        notice = notice
                    ),
                    code
                )
            } else if (code == 404) {
                NetworkResult.Success(
                    RemoteTokenVerification(
                        valid = false,
                        verdict = "NOT_FOUND",
                        reason = "No such verification token exists."
                    ),
                    code
                )
            } else {
                NetworkResult.Error(code, "Token verification failed (HTTP $code): $body")
            }
        }
    }

    /**
     * Verifies a student credential against its cryptographic seal:
     * GET /api/verify/{apaarId}?seal={seal}
     */
    fun verifySeal(
        apaarId: String,
        seal: String,
        authToken: String? = null,
        baseUrl: String = defaultBaseUrl
    ): NetworkResult<String> {
        val cleanBase = baseUrl.trimEnd('/')
        val url = "$cleanBase/verify/${encodeUri(apaarId)}?seal=${encodeUri(seal)}"

        return executeGet(url, authToken) { body, code ->
            if (code in 200..299) {
                val verdict = extractString(body, "verdict") ?: "VALID"
                NetworkResult.Success(verdict, code)
            } else {
                NetworkResult.Error(code, "Seal verification failed (HTTP $code): $body")
            }
        }
    }

    /**
     * Fetches students list from the central registry:
     * GET /api/students?limit={limit}&skip={skip}
     */
    fun fetchStudents(
        authToken: String? = null,
        limit: Int = 50,
        skip: Int = 0,
        baseUrl: String = defaultBaseUrl
    ): NetworkResult<List<RemoteStudentDto>> {
        val cleanBase = baseUrl.trimEnd('/')
        val url = "$cleanBase/students?limit=$limit&skip=$skip"

        return executeGet(url, authToken) { body, code ->
            if (code in 200..299) {
                val students = parseStudentList(body)
                NetworkResult.Success(students, code)
            } else {
                NetworkResult.Error(code, "Failed to fetch students (HTTP $code)")
            }
        }
    }

    /**
     * Submits or synchronizes a student record to the backend:
     * POST /api/students
     */
    fun submitStudent(
        student: RemoteStudentDto,
        authToken: String? = null,
        baseUrl: String = defaultBaseUrl
    ): NetworkResult<RemoteStudentDto> {
        val cleanBase = baseUrl.trimEnd('/')
        val url = "$cleanBase/students"
        val jsonPayload = serializeStudent(student)

        return executePost(url, jsonPayload, authToken) { body, code ->
            when (code) {
                in 200..299 -> {
                    NetworkResult.Success(student.copy(recordId = extractString(body, "record_id") ?: student.recordId), code)
                }
                409 -> {
                    NetworkResult.Error(409, "Duplicate submission: student APAAR ${student.apaarId} already enrolled")
                }
                422 -> {
                    NetworkResult.Error(422, "Validation failed: ${extractString(body, "detail") ?: body}")
                }
                else -> {
                    NetworkResult.Error(code, "Server returned HTTP $code: $body")
                }
            }
        }
    }

    // ------------------------------------------------------------- Core HTTP helpers

    private fun <T> executeGet(
        urlString: String,
        authToken: String? = null,
        parser: (String, Int) -> NetworkResult<T>
    ): NetworkResult<T> {
        return try {
            val url = URL(urlString)
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = connectTimeoutMs
                readTimeout = readTimeoutMs
                setRequestProperty("Accept", "application/json")
                if (!authToken.isNullOrBlank()) {
                    setRequestProperty("Authorization", "Bearer $authToken")
                }
            }

            val statusCode = conn.responseCode
            val isSuccess = statusCode in 200..299
            val stream = if (isSuccess) conn.inputStream else (conn.errorStream ?: conn.inputStream)
            val body = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()

            parser(body, statusCode)
        } catch (e: java.io.IOException) {
            NetworkResult.OfflineFallback(
                reason = "Network unavailable: ${e.message ?: "Connection failed"}"
            )
        } catch (e: Exception) {
            NetworkResult.Error(
                statusCode = -1,
                message = e.message ?: "Unexpected network error",
                cause = e
            )
        }
    }

    private fun <T> executePost(
        urlString: String,
        jsonBody: String,
        authToken: String? = null,
        parser: (String, Int) -> NetworkResult<T>
    ): NetworkResult<T> {
        return try {
            val url = URL(urlString)
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                doOutput = true
                connectTimeout = connectTimeoutMs
                readTimeout = readTimeoutMs
                setRequestProperty("Content-Type", "application/json; charset=utf-8")
                setRequestProperty("Accept", "application/json")
                if (!authToken.isNullOrBlank()) {
                    setRequestProperty("Authorization", "Bearer $authToken")
                }
            }

            OutputStreamWriter(conn.outputStream, StandardCharsets.UTF_8).use { writer ->
                writer.write(jsonBody)
                writer.flush()
            }

            val statusCode = conn.responseCode
            val isSuccess = statusCode in 200..299
            val stream = if (isSuccess) conn.inputStream else (conn.errorStream ?: conn.inputStream)
            val body = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()

            parser(body, statusCode)
        } catch (e: java.io.IOException) {
            NetworkResult.OfflineFallback(
                reason = "Network unavailable: ${e.message ?: "Connection failed"}"
            )
        } catch (e: Exception) {
            NetworkResult.Error(
                statusCode = -1,
                message = e.message ?: "Unexpected network error",
                cause = e
            )
        }
    }

    // ------------------------------------------------------------- Zero-dependency JSON Parsing

    fun extractString(json: String, key: String): String? {
        val pattern = Regex("\"$key\"\\s*:\\s*\"([^\"]*)\"")
        return pattern.find(json)?.groupValues?.get(1)
    }

    fun extractBoolean(json: String, key: String): Boolean? {
        val pattern = Regex("\"$key\"\\s*:\\s*(true|false)")
        return pattern.find(json)?.groupValues?.get(1)?.toBoolean()
    }

    fun extractLong(json: String, key: String): Long? {
        val pattern = Regex("\"$key\"\\s*:\\s*(\\d+)")
        return pattern.find(json)?.groupValues?.get(1)?.toLongOrNull()
    }

    fun serializeStudent(student: RemoteStudentDto): String {
        return buildString {
            append("{")
            append("\"apaar_id\":\"").append(escapeJson(student.apaarId)).append("\",")
            append("\"student_name\":\"").append(escapeJson(student.studentName)).append("\",")
            append("\"date_of_birth\":\"").append(escapeJson(student.dateOfBirth)).append("\",")
            append("\"gender\":\"").append(escapeJson(student.gender)).append("\",")
            append("\"institution_id\":\"").append(escapeJson(student.institutionId)).append("\",")
            append("\"program_id\":\"").append(escapeJson(student.programId)).append("\",")
            append("\"academic_year\":\"").append(escapeJson(student.academicYear)).append("\",")
            append("\"admission_quota\":\"").append(escapeJson(student.admissionQuota)).append("\",")
            append("\"enrollment_date\":\"").append(escapeJson(student.enrollmentDate)).append("\",")
            append("\"student_institute_roll_no\":\"").append(escapeJson(student.studentInstituteRollNo)).append("\",")
            append("\"nationality\":\"").append(escapeJson(student.nationality)).append("\"")
            if (student.passportNumber != null) {
                append(",\"passport_number\":\"").append(escapeJson(student.passportNumber)).append("\"")
            }
            append("}")
        }
    }

    fun parseStudentList(json: String): List<RemoteStudentDto> {
        val list = mutableListOf<RemoteStudentDto>()
        // Splits by objects { ... }
        val objectRegex = Regex("\\{[^{}]+\\}")
        for (match in objectRegex.findAll(json)) {
            val obj = match.value
            val apaar = extractString(obj, "apaar_id") ?: continue
            val name = extractString(obj, "student_name") ?: ""
            val dob = extractString(obj, "date_of_birth") ?: ""
            val gender = extractString(obj, "gender") ?: "OTHER"
            val inst = extractString(obj, "institution_id") ?: ""
            val prog = extractString(obj, "program_id") ?: ""
            val year = extractString(obj, "academic_year") ?: ""
            val quota = extractString(obj, "admission_quota") ?: "MERIT"
            val enrollDate = extractString(obj, "enrollment_date") ?: ""
            val roll = extractString(obj, "student_institute_roll_no") ?: ""
            val nationality = extractString(obj, "nationality") ?: "Indian"
            val status = extractString(obj, "verification_status") ?: "PENDING_REVIEW"
            val id = extractString(obj, "record_id") ?: extractString(obj, "_id") ?: ""

            list += RemoteStudentDto(
                recordId = id,
                apaarId = apaar,
                studentName = name,
                dateOfBirth = dob,
                gender = gender,
                institutionId = inst,
                programId = prog,
                academicYear = year,
                admissionQuota = quota,
                enrollmentDate = enrollDate,
                studentInstituteRollNo = roll,
                nationality = nationality,
                verificationStatus = status
            )
        }
        return list
    }

    private fun escapeJson(str: String): String =
        str.replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")

    private fun encodeUri(str: String): String {
        return java.net.URLEncoder.encode(str, "UTF-8").replace("+", "%20")
    }
}
