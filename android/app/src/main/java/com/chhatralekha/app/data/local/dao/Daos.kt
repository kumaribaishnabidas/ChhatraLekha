package com.chhatralekha.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.chhatralekha.app.data.local.entity.AnomalyRecordEntity
import com.chhatralekha.app.data.local.entity.AuditLogEntity
import com.chhatralekha.app.data.local.entity.InstitutionEntity
import com.chhatralekha.app.data.local.entity.ProgramIntakeEntity
import com.chhatralekha.app.data.local.entity.StudentEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface InstitutionDao {
    @Query("SELECT * FROM institutions ORDER BY name")
    fun observeAll(): Flow<List<InstitutionEntity>>

    @Query("SELECT * FROM institutions ORDER BY name")
    suspend fun getAll(): List<InstitutionEntity>

    @Query("SELECT * FROM institutions WHERE institutionId = :id")
    suspend fun getById(id: String): InstitutionEntity?

    @Query("SELECT COUNT(*) FROM institutions")
    suspend fun count(): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<InstitutionEntity>)
}

@Dao
interface ProgramIntakeDao {
    @Query("SELECT * FROM program_intakes ORDER BY programName")
    fun observeAll(): Flow<List<ProgramIntakeEntity>>

    @Query("SELECT * FROM program_intakes")
    suspend fun getAll(): List<ProgramIntakeEntity>

    @Query("SELECT * FROM program_intakes WHERE institutionId = :institutionId ORDER BY programName")
    fun observeByInstitution(institutionId: String): Flow<List<ProgramIntakeEntity>>

    @Query("SELECT * FROM program_intakes WHERE institutionId = :institutionId")
    suspend fun getByInstitution(institutionId: String): List<ProgramIntakeEntity>

    @Query("SELECT COUNT(*) FROM program_intakes")
    suspend fun count(): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<ProgramIntakeEntity>)
}

@Dao
interface StudentDao {
    @Query("SELECT * FROM students ORDER BY studentName")
    fun observeAll(): Flow<List<StudentEntity>>

    @Query("SELECT * FROM students")
    suspend fun getAll(): List<StudentEntity>

    @Query("SELECT * FROM students WHERE institutionId = :institutionId ORDER BY studentName")
    fun observeByInstitution(institutionId: String): Flow<List<StudentEntity>>

    @Query("SELECT * FROM students WHERE institutionId = :institutionId")
    suspend fun getByInstitution(institutionId: String): List<StudentEntity>

    @Query(
        "SELECT * FROM students WHERE apaarId = :apaarId AND isActive = 1 " +
            "ORDER BY CASE WHEN verificationStatus = 'VERIFIED' THEN 0 ELSE 1 END, enrollmentDate"
    )
    suspend fun getActiveByApaarId(apaarId: String): List<StudentEntity>

    @Query("SELECT * FROM students WHERE studentInstituteRollNo = :rollNo LIMIT 1")
    suspend fun getByRollNo(rollNo: String): StudentEntity?

    @Query("SELECT * FROM students WHERE recordId = :recordId")
    suspend fun getByRecordId(recordId: Long): StudentEntity?

    @Query("SELECT COUNT(*) FROM students")
    suspend fun count(): Int

    @Query("SELECT COUNT(*) FROM students WHERE apaarId = :apaarId")
    suspend fun countByApaarId(apaarId: String): Int

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insert(item: StudentEntity): Long

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertAll(items: List<StudentEntity>): List<Long>

    @Update
    suspend fun update(item: StudentEntity)

    @Query("UPDATE students SET verificationStatus = :status WHERE recordId = :recordId")
    suspend fun updateVerificationStatus(recordId: Long, status: String)
}

@Dao
interface AnomalyDao {
    @Query("SELECT * FROM anomaly_records ORDER BY timestamp DESC")
    fun observeAll(): Flow<List<AnomalyRecordEntity>>

    @Query("SELECT * FROM anomaly_records ORDER BY timestamp DESC")
    suspend fun getAll(): List<AnomalyRecordEntity>

    @Query("SELECT COUNT(*) FROM anomaly_records")
    suspend fun count(): Int

    @Query("DELETE FROM anomaly_records")
    suspend fun clear()

    @Insert
    suspend fun insertAll(items: List<AnomalyRecordEntity>)
}

@Dao
interface AuditLogDao {
    @Query("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT :limit")
    fun observeRecent(limit: Int = 200): Flow<List<AuditLogEntity>>

    @Query("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getRecent(limit: Int = 200): List<AuditLogEntity>

    @Query("SELECT COUNT(*) FROM audit_logs")
    suspend fun count(): Int

    @Insert
    suspend fun insert(item: AuditLogEntity)

    @Insert
    suspend fun insertAll(items: List<AuditLogEntity>)
}
