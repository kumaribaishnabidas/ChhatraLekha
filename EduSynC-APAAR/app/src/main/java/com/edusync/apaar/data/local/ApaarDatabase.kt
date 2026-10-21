package com.edusync.apaar.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.edusync.apaar.data.local.dao.AnomalyDao
import com.edusync.apaar.data.local.dao.AuditLogDao
import com.edusync.apaar.data.local.dao.InstitutionDao
import com.edusync.apaar.data.local.dao.ProgramIntakeDao
import com.edusync.apaar.data.local.dao.StudentDao
import com.edusync.apaar.data.local.entity.AnomalyRecordEntity
import com.edusync.apaar.data.local.entity.AuditLogEntity
import com.edusync.apaar.data.local.entity.InstitutionEntity
import com.edusync.apaar.data.local.entity.ProgramIntakeEntity
import com.edusync.apaar.data.local.entity.StudentEntity

@Database(
    entities = [
        InstitutionEntity::class,
        ProgramIntakeEntity::class,
        StudentEntity::class,
        AnomalyRecordEntity::class,
        AuditLogEntity::class
    ],
    version = 1,
    exportSchema = true
)
abstract class ApaarDatabase : RoomDatabase() {

    abstract fun institutionDao(): InstitutionDao
    abstract fun programIntakeDao(): ProgramIntakeDao
    abstract fun studentDao(): StudentDao
    abstract fun anomalyDao(): AnomalyDao
    abstract fun auditLogDao(): AuditLogDao

    companion object {
        private const val DATABASE_NAME = "apaar-registry.db"

        @Volatile
        private var instance: ApaarDatabase? = null

        fun get(context: Context): ApaarDatabase = instance ?: synchronized(this) {
            instance ?: Room.databaseBuilder(
                context.applicationContext,
                ApaarDatabase::class.java,
                DATABASE_NAME
            ).fallbackToDestructiveMigration().build().also { instance = it }
        }
    }
}
