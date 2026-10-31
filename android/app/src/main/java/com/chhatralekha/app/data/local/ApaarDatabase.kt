package com.chhatralekha.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.chhatralekha.app.data.local.dao.AnomalyDao
import com.chhatralekha.app.data.local.dao.AuditLogDao
import com.chhatralekha.app.data.local.dao.InstitutionDao
import com.chhatralekha.app.data.local.dao.ProgramIntakeDao
import com.chhatralekha.app.data.local.dao.StudentDao
import com.chhatralekha.app.data.local.entity.AnomalyRecordEntity
import com.chhatralekha.app.data.local.entity.AuditLogEntity
import com.chhatralekha.app.data.local.entity.InstitutionEntity
import com.chhatralekha.app.data.local.entity.ProgramIntakeEntity
import com.chhatralekha.app.data.local.entity.StudentEntity

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
