# ChhatraLekha — Mobile Alignment: Shared Platform Foundation

This document defines the cross-platform entity mapping, local database models, push notification contracts, and navigation paradigms across Android (Kotlin / Jetpack Compose / Room) and iOS (Swift 6 / SwiftUI / GRDB).

---

## 1. Cross-Platform Entity Architecture

The Shared Platform Foundation introduces four primary domain entities in the backend (`app/modules/profiles/` and `app/modules/notifications/`):
1. **UserProfile**: Core identity decoupled from institutional roles.
2. **InstitutionMembership**: Multi-tenant institutional affiliations, roles, and departments.
3. **Notification**: In-app notifications with category classification and zero-PII deep links.
4. **NotificationPreference**: Quiet hours schedule and channel delivery configurations.

### Entity Mapping Matrix

| Backend Schema (Pydantic / Mongo) | Android Entity (Kotlin / Room) | iOS Model (Swift 6 / GRDB) |
|---|---|---|
| `UserProfile` | `UserProfileEntity` (`@Entity(tableName = "user_profiles")`) | `UserProfileRecord` (`Record, Codable, Sendable`) |
| `ProfileImage` | Embedded fields in `UserProfileEntity` (`commonUrl`, `androidUrl`, `webUrl`, `iosUrl`, `useCommon`) | Embedded struct `ProfileImageSet` |
| `UserEmail` | `UserEmailEntity` (`@Entity(tableName = "user_emails")`) | `UserEmailRecord` (`Record, Codable, Sendable`) |
| `InstitutionMembership` | `InstitutionMembershipEntity` (`@Entity(tableName = "institution_memberships")`) | `InstitutionMembershipRecord` (`Record, Codable, Sendable`) |
| `Notification` | `NotificationEntity` (`@Entity(tableName = "notifications")`) | `NotificationRecord` (`Record, Codable, Sendable`) |
| `NotificationPreference` | `NotificationPreferenceEntity` (`@Entity(tableName = "notification_preferences")`) | `NotificationPreferenceRecord` (`Record, Codable, Sendable`) |

---

## 2. Android (Kotlin / Room) Implementation

### 2.1 Room Entities (`Entities.kt`)

```kotlin
package com.chhatralekha.app.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * User core profile identity.
 */
@Entity(
    tableName = "user_profiles",
    indices = [Index("userId", unique = true), Index("primaryEmail")]
)
data class UserProfileEntity(
    @PrimaryKey val userId: String,
    val fullName: String,
    val displayName: String?,
    val primaryEmail: String,
    val phone: String?,
    val bio: String?,
    val avatarCommonUrl: String?,
    val avatarWebUrl: String?,
    val avatarAndroidUrl: String?,
    val avatarIosUrl: String?,
    val useCommonAvatar: Boolean = true,
    val preferredLanguage: String = "en",
    val highContrast: Boolean = false,
    val reducedMotion: Boolean = false,
    val screenReaderOptimized: Boolean = false,
    val profileCompletionPercentage: Int = 50,
    val accountStatus: String = "ACTIVE",
    val lastSyncTimestamp: Long = System.currentTimeMillis()
) {
    /**
     * Resolves the platform-tailored avatar for Android.
     */
    fun resolveActiveAvatarUrl(): String? {
        return if (useCommonAvatar) {
            avatarCommonUrl ?: avatarAndroidUrl
        } else {
            avatarAndroidUrl ?: avatarCommonUrl
        }
    }
}

/**
 * Multi-institution membership association.
 */
@Entity(
    tableName = "institution_memberships",
    primaryKeys = ["userId", "institutionId"],
    indices = [Index("userId"), Index("institutionId")]
)
data class InstitutionMembershipEntity(
    val userId: String,
    val institutionId: String,
    val institutionName: String,
    val role: String,
    val department: String?,
    val designation: String?,
    val academicYear: String?,
    val isPrimary: Boolean = false,
    val status: String = "ACTIVE"
)

/**
 * Cached in-app notification with zero-PII deep linking.
 */
@Entity(
    tableName = "notifications",
    indices = [
        Index("notificationId", unique = true),
        Index("userId"),
        Index("category"),
        Index("isRead")
    ]
)
data class NotificationEntity(
    @PrimaryKey val notificationId: String,
    val userId: String,
    val institutionId: String?,
    val category: String, // ACADEMIC, ATTENDANCE, EXAMINATIONS, ANNOUNCEMENTS, SYSTEM
    val priority: String, // LOW, NORMAL, HIGH, URGENT
    val title: String,
    val message: String,
    val deepLink: String?,
    val isRead: Boolean = false,
    val createdAt: Long,
    val readAt: Long?
)

/**
 * Local device notification preferences and quiet hours.
 */
@Entity(tableName = "notification_preferences")
data class NotificationPreferenceEntity(
    @PrimaryKey val userId: String,
    val inAppEnabled: Boolean = true,
    val pushEnabled: Boolean = true,
    val emailEnabled: Boolean = false,
    val quietHoursEnabled: Boolean = true,
    val quietHoursStart: String = "22:00",
    val quietHoursEnd: String = "07:00",
    val notifyAttendance: Boolean = true,
    val notifyExaminations: Boolean = true,
    val notifyAssignments: Boolean = true,
    val notifyAnnouncements: Boolean = true
)
```

### 2.2 Room Data Access Objects (`Daos.kt`)

```kotlin
package com.chhatralekha.app.data.local.dao

import androidx.room.*
import com.chhatralekha.app.data.local.entity.*
import kotlinx.coroutines.flow.Flow

@Dao
interface UserProfileDao {
    @Query("SELECT * FROM user_profiles WHERE userId = :userId LIMIT 1")
    fun observeProfile(userId: String): Flow<UserProfileEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertProfile(profile: UserProfileEntity)

    @Query("SELECT * FROM institution_memberships WHERE userId = :userId")
    fun observeMemberships(userId: String): Flow<List<InstitutionMembershipEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun replaceMemberships(memberships: List<InstitutionMembershipEntity>)
}

@Dao
interface NotificationDao {
    @Query("SELECT * FROM notifications WHERE userId = :userId ORDER BY createdAt DESC")
    fun observeNotifications(userId: String): Flow<List<NotificationEntity>>

    @Query("SELECT COUNT(*) FROM notifications WHERE userId = :userId AND isRead = 0")
    fun observeUnreadCount(userId: String): Flow<Int>

    @Query("UPDATE notifications SET isRead = 1, readAt = :now WHERE notificationId = :id")
    suspend fun markAsRead(id: String, now: Long = System.currentTimeMillis())

    @Query("UPDATE notifications SET isRead = 1, readAt = :now WHERE userId = :userId AND isRead = 0")
    suspend fun markAllAsRead(userId: String, now: Long = System.currentTimeMillis())

    @Query("DELETE FROM notifications WHERE notificationId = :id")
    suspend fun deleteNotification(id: String)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertNotifications(notifications: List<NotificationEntity>)
}
```

---

## 3. iOS (Swift 6 / GRDB) Implementation

### 3.1 Domain & Persistence Models (`DomainModels.swift`)

```swift
import Foundation
import GRDB

public struct UserProfileRecord: Codable, FetchableRecord, PersistableRecord, Sendable, Identifiable {
    public static let databaseTableName = "user_profiles"

    public var id: String { userId }
    public let userId: String
    public var fullName: String
    public var displayName: String?
    public var primaryEmail: String
    public var phone: String?
    public var bio: String?
    public var avatarCommonUrl: String?
    public var avatarWebUrl: String?
    public var avatarAndroidUrl: String?
    public var avatarIosUrl: String?
    public var useCommonAvatar: Bool
    public var preferredLanguage: String
    public var highContrast: Bool
    public var reducedMotion: Bool
    public var screenReaderOptimized: Bool
    public var profileCompletionPercentage: Int
    public var accountStatus: String
    public var lastSyncTimestamp: Date

    /// Resolves the platform-tailored avatar for iOS.
    public var activeAvatarURL: URL? {
        let urlStr = useCommonAvatar
            ? (avatarCommonUrl ?? avatarIosUrl)
            : (avatarIosUrl ?? avatarCommonUrl)
        guard let urlStr else { return nil }
        return URL(string: urlStr)
    }
}

public struct InstitutionMembershipRecord: Codable, FetchableRecord, PersistableRecord, Sendable, Identifiable {
    public static let databaseTableName = "institution_memberships"

    public var id: String { "\(userId)-\(institutionId)" }
    public let userId: String
    public let institutionId: String
    public let institutionName: String
    public let role: String
    public let department: String?
    public let designation: String?
    public let academicYear: String?
    public let isPrimary: Bool
    public let status: String
}

public struct NotificationRecord: Codable, FetchableRecord, PersistableRecord, Sendable, Identifiable {
    public static let databaseTableName = "notifications"

    public var id: String { notificationId }
    public let notificationId: String
    public let userId: String
    public let institutionId: String?
    public let category: String
    public let priority: String
    public let title: String
    public let message: String
    public let deepLink: String?
    public var isRead: Bool
    public let createdAt: Date
    public var readAt: Date?
}

public struct NotificationPreferenceRecord: Codable, FetchableRecord, PersistableRecord, Sendable {
    public static let databaseTableName = "notification_preferences"

    public let userId: String
    public var inAppEnabled: Bool
    public var pushEnabled: Bool
    public var emailEnabled: Bool
    public var quietHoursEnabled: Bool
    public var quietHoursStart: String // "22:00"
    public var quietHoursEnd: String   // "07:00"
    public var notifyAttendance: Bool
    public var notifyExaminations: Bool
    public var notifyAssignments: Bool
    public var notifyAnnouncements: Bool
}
```

---

## 4. Push Notification Contract (FCM / APNs)

Push notifications carry zero sensitive personal information (PII) to comply with DPDP Act 2023.

### Unified Push Payload Format

```json
{
  "to": "device_registration_token",
  "priority": "high",
  "notification": {
    "title": "Examination Timetable Published",
    "body": "Mid-term schedule published by the academic office."
  },
  "data": {
    "notification_id": "ntf-90214",
    "category": "EXAMINATIONS",
    "institution_id": "INST-0421",
    "deep_link": "chhatralekha://results",
    "priority": "HIGH",
    "created_at": "2026-11-06T10:00:00Z"
  }
}
```

### Quiet Hours Local Suppression Algorithm
When a push notification arrives on either Android or iOS:
1. The client background worker inspects `quietHoursEnabled`.
2. If `true` and the current local wall time falls between `quietHoursStart` (e.g. `22:00`) and `quietHoursEnd` (e.g. `07:00`):
   - For `NORMAL` or `LOW` priority notifications: suppress audible sound and vibration. Save silently to the local database.
   - For `URGENT` priority notifications (e.g. campus emergency): bypass quiet hours and play the alert tone.

---

## 5. Mobile Navigation Parity Matrix

Both mobile platforms replicate the permission-aware navigation tree:

| Destination | Route / Identifier | Android Compose Navigation | iOS SwiftUI Tab / Link | Permission Gate |
|---|---|---|---|---|
| Dashboard / Home | `home` | `ApaarAppNavRoute.Home` | `HomeView()` | Authenticated |
| Academics & Syllabus | `academics` | `ApaarAppNavRoute.Academics` | `AcademicsView()` | Authenticated |
| Attendance Register | `attendance` | `ApaarAppNavRoute.Attendance` | `AttendanceView()` | `RECORD_ATTENDANCE` / `VIEW_OWN_RECORD` |
| Examinations & Results | `results` | `ApaarAppNavRoute.Results` | `ResultsView()` | `VIEW_RESULTS` / `VIEW_OWN_RECORD` |
| Verifiable ID Card | `id_card` | `ApaarAppNavRoute.IdCard` | `IdCardView()` | `VIEW_OWN_RECORD` |
| Notification Centre | `notifications` | `ApaarAppNavRoute.Notifications` | `NotificationsView()` | Authenticated |
| User Profile & Account | `profile` | `ApaarAppNavRoute.Profile` | `ProfileView()` | Authenticated |

---

## 6. Offline Synchronization & Mutation Protocol

1. **Avatar Upload**: When the user captures or uploads a platform avatar offline, it is saved in encrypted local cache (`app_specific_storage`). A mutation task is queued with a local URI. Upon network recovery, the background sync worker uploads the file to `/api/profiles/avatar/{platform}` using multipart form data.
2. **Notification Reads**: Marking an item as read offline updates the local Room / GRDB store immediately. The mutation is added to the outbox table (`pending_mutations`), and synced to `PUT /api/notifications/{id}/read` upon network availability.
3. **Multi-Institution Context**: Active institution selection is persisted in local device preferences (`EncryptedSharedPreferences` on Android / `UserDefaults` with Keychain-backed token on iOS) and included in the `X-Institution-ID` header on all outbound API requests.

