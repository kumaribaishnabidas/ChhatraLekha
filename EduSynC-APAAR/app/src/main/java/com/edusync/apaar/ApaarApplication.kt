package com.edusync.apaar

import android.app.Application
import com.edusync.apaar.data.local.ApaarDatabase
import com.edusync.apaar.data.repository.ApaarRepository

/**
 * Application-scoped dependency container.
 *
 * The platform is fully offline: the Room database and the repository that
 * mediates it are created once here and shared by every screen.
 */
class ApaarApplication : Application() {

    /** The local APAAR registry database. */
    val database: ApaarDatabase by lazy { ApaarDatabase.get(this) }

    /** The single repository instance used by the whole UI layer. */
    val repository: ApaarRepository by lazy { ApaarRepository(database) }
}
