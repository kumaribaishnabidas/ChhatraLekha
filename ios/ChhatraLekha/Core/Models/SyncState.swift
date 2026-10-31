import Foundation

/// Synchronization status of local offline records against remote server.
public enum SyncStatus: String, Codable {
    case synced = "SYNCED"
    case pending = "PENDING"
    case inFlight = "IN_FLIGHT"
    case failed = "FAILED"
    case conflict = "CONFLICT"

    public var displayLabel: String {
        switch self {
        case .synced:
            return "Synced"
        case .pending:
            return "Pending Sync"
        case .inFlight:
            return "Syncing..."
        case .failed:
            return "Sync Failed"
        case .conflict:
            return "Conflict Detected"
        }
    }
}

/// A queued mutation performed offline requiring remote synchronization.
public struct QueuedMutation: Codable, Identifiable {
    public let id: String
    public let endpoint: String
    public let method: String
    public let payloadJson: String
    public let createdAt: Date
    public var retryCount: Int
    public var status: SyncStatus

    public init(
        id: String = UUID().uuidString,
        endpoint: String,
        method: String = "POST",
        payloadJson: String,
        createdAt: Date = Date(),
        retryCount: Int = 0,
        status: SyncStatus = .pending
    ) {
        self.id = id
        self.endpoint = endpoint
        self.method = method
        self.payloadJson = payloadJson
        self.createdAt = createdAt
        self.retryCount = retryCount
        self.status = status
    }
}

