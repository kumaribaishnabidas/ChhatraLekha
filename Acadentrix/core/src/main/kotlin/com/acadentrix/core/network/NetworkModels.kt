package com.acadentrix.core.network

/**
 * Result wrapper for all network interactions between the Android client
 * and the ChhatraLekha backend API.
 */
sealed class NetworkResult<out T> {
    data class Success<out T>(val data: T, val statusCode: Int = 200) : NetworkResult<T>()
    data class OfflineFallback(val reason: String) : NetworkResult<Nothing>()
    data class Error(val statusCode: Int, val message: String, val cause: Throwable? = null) : NetworkResult<Nothing>()

    val isSuccess: Boolean get() = this is Success
    val isOffline: Boolean get() = this is OfflineFallback
    val isError: Boolean get() = this is Error

    fun getOrNull(): T? = when (this) {
        is Success -> data
        is OfflineFallback -> null
        is Error -> null
    }
}


/**
 * Public response returned by the backend for an opaque verification token.
 * Contains only the allowlisted fields.
 */
data class RemoteTokenVerification(
    val valid: Boolean,
    val verdict: String,
    val reason: String,
    val institution: String? = null,
    val programme: String? = null,
    val academicYear: String? = null,
    val recordStatus: String? = null,
    val issuedAt: Long? = null,
    val expiresAt: Long? = null,
    val notice: String? = null
)

/**
 * DTO representing a student record exchanged with the backend.
 */
data class RemoteStudentDto(
    val recordId: String = "",
    val apaarId: String,
    val studentName: String,
    val dateOfBirth: String,
    val gender: String,
    val institutionId: String,
    val programId: String,
    val academicYear: String,
    val admissionQuota: String = "MERIT",
    val enrollmentDate: String,
    val studentInstituteRollNo: String = "",
    val nationality: String = "Indian",
    val passportNumber: String? = null,
    val visaValidity: String? = null,
    val countryOfOrigin: String? = null,
    val verificationStatus: String = "PENDING_REVIEW",
    val isActive: Boolean = true
)

/**
 * Summary of a synchronization operation between local Room storage and backend.
 */
data class SyncSummary(
    val pulledCount: Int = 0,
    val pushedCount: Int = 0,
    val conflictsCount: Int = 0,
    val isOffline: Boolean = false,
    val message: String = ""
)
