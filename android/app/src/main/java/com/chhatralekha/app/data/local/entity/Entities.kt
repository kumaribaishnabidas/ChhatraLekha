package com.chhatralekha.app.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * An AICTE-approved institution.
 *
 * [institutionId] is the AICTE Permanent Identifier (PID), e.g. `1-332491024`.
 */
@Entity(tableName = "institutions")
data class InstitutionEntity(
    @PrimaryKey val institutionId: String,
    val name: String,
    val institutionType: String,
    val state: String,
    val city: String,
    val affiliationUniversity: String,
    val approvalYear: Int,
    val naacGrade: String
)

/**
 * Sanctioned capacity for one programme of one institution.
 *
 * The composite key (institutionId, programId) allows the same AICTE programme
 * code to exist across many institutions — exactly as in the national registry.
 */
@Entity(
    tableName = "program_intakes",
    primaryKeys = ["institutionId", "programId"],
    indices = [Index("institutionId")]
)
data class ProgramIntakeEntity(
    val institutionId: String,
    val programId: String,
    val programName: String,
    val programLevel: String,
    val approvedIntake: Int,
    val maxSupernumeraryNri: Int,
    val maxSupernumeraryFnOci: Int,
    val maxSupernumeraryTfw: Int,
    val maxPmsss: Int
)

/**
 * A student enrolment.
 *
 * Note: `apaarId` is **indexed but not unique**. The national registry must be able
 * to physically store the same APAAR ID claimed by two institutions so that the
 * cross-institutional duplicate check can fire — a unique constraint would simply
 * hide the very anomaly we are required to detect.
 */
@Entity(
    tableName = "students",
    indices = [
        Index("apaarId"),
        Index("institutionId"),
        Index("programId"),
        Index(value = ["institutionId", "programId"])
    ]
)
data class StudentEntity(
    @PrimaryKey(autoGenerate = true) val recordId: Long = 0,
    val apaarId: String,
    val studentName: String,
    val dateOfBirth: String,
    val gender: String,
    val institutionId: String,
    val programId: String,
    val academicYear: String,
    val admissionQuota: String,
    val enrollmentDate: String,
    val studentInstituteRollNo: String,
    val nationality: String,
    val passportNumber: String?,
    val visaValidity: String?,
    val countryOfOrigin: String?,
    val abcAccountId: String?,
    val verificationStatus: String,
    val isActive: Boolean = true,
    val photoSeed: Int = 0
)

/**
 * A detected regulatory anomaly.
 */
@Entity(
    tableName = "anomaly_records",
    indices = [Index("studentApaarId"), Index("institutionId"), Index("anomalyType")]
)
data class AnomalyRecordEntity(
    @PrimaryKey(autoGenerate = true) val anomalyId: Long = 0,
    val studentApaarId: String,
    val institutionId: String,
    val programId: String?,
    val anomalyType: String,
    val severity: String,
    val details: String,
    val timestamp: Long,
    val resolved: Boolean = false
)

/**
 * Immutable regulatory audit trail.
 */
@Entity(tableName = "audit_logs", indices = [Index("timestamp")])
data class AuditLogEntity(
    @PrimaryKey(autoGenerate = true) val logId: Long = 0,
    val timestamp: Long,
    val actor: String,
    val action: String,
    val subject: String,
    val details: String,
    val category: String
)
