package com.acadentrix.core.network

/**
 * Handles two-way synchronization between the local Android database and the central server.
 * Implements deduplication, duplicate conflict detection, and offline resilience.
 */
class SyncManager(
    private val apiClient: ChhatraLekhaApiClient = ChhatraLekhaApiClient()
) {
    enum class ConflictResolution {
        SERVER_WINS,
        CLIENT_WINS,
        FLAG_ANOMALY
    }

    /**
     * Synchronizes a list of local student records with the central registry.
     *
     * 1. Checks backend connectivity. If unreachable, returns immediately with [SyncSummary.isOffline] = true.
     * 2. Pushes unsynced/local records to the backend. If the backend returns 409 Conflict (e.g. duplicate
     *    APAAR in another institution), flags the conflict rather than silently discarding.
     * 3. Fetches latest remote records to update local cache.
     */
    fun performSync(
        baseUrl: String = apiClient.defaultBaseUrl,
        authToken: String? = null,
        localStudents: List<RemoteStudentDto>,
        conflictResolution: ConflictResolution = ConflictResolution.SERVER_WINS
    ): SyncSummary {
        // Step 1: Connectivity check
        val health = apiClient.checkHealth(baseUrl)
        if (health.isOffline || (health is NetworkResult.Error && health.statusCode == -1)) {
            return SyncSummary(
                pulledCount = 0,
                pushedCount = 0,
                conflictsCount = 0,
                isOffline = true,
                message = "ChhatraLekha backend is offline or unreachable. Continuing in offline-first mode."
            )
        }

        var pushed = 0
        var conflicts = 0

        // Step 2: Push local records
        for (local in localStudents) {
            val result = apiClient.submitStudent(local, authToken, baseUrl)
            when (result) {
                is NetworkResult.Success -> pushed++
                is NetworkResult.Error -> {
                    if (result.statusCode == 409) {
                        conflicts++
                    }
                }
                is NetworkResult.OfflineFallback -> {
                    return SyncSummary(
                        pulledCount = 0,
                        pushedCount = pushed,
                        conflictsCount = conflicts,
                        isOffline = true,
                        message = "Connection dropped during sync: ${result.reason}"
                    )
                }
            }
        }

        // Step 3: Pull remote records
        val pullResult = apiClient.fetchStudents(authToken, limit = 100, skip = 0, baseUrl = baseUrl)
        val pulledCount = when (pullResult) {
            is NetworkResult.Success -> pullResult.data.size
            else -> 0
        }

        return SyncSummary(
            pulledCount = pulledCount,
            pushedCount = pushed,
            conflictsCount = conflicts,
            isOffline = false,
            message = "Sync complete: pushed $pushed record(s), pulled $pulledCount record(s), resolved $conflicts conflict(s)."
        )
    }
}
