import Foundation
import Combine

/// Manages offline-first operation queues, automatic retries, and synchronization.
public final class SyncQueue: ObservableObject {
    public static let shared = SyncQueue()

    @Published public private(set) var pendingMutations: [QueuedMutation] = []
    @Published public private(set) var currentSyncStatus: SyncStatus = .synced
    @Published public private(set) var lastSyncDate: Date?

    private let storeKey = "queued_mutations.json"
    private let queue = DispatchQueue(label: "com.chhatralekha.app.syncqueue")

    private init() {
        loadPersistedQueue()
    }

    public func enqueue(endpoint: String, method: String = "POST", payloadJson: String) {
        let mutation = QueuedMutation(
            endpoint: endpoint,
            method: method,
            payloadJson: payloadJson,
            status: .pending
        )
        queue.async { [weak self] in
            guard let self = self else { return }
            self.pendingMutations.append(mutation)
            self.persistQueue()
            DispatchQueue.main.async {
                self.currentSyncStatus = .pending
            }
        }
    }

    public func processQueue(apiClient: ApiClient) async {
        guard !pendingMutations.isEmpty else {
            await MainActor.run {
                self.currentSyncStatus = .synced
            }
            return
        }

        await MainActor.run {
            self.currentSyncStatus = .inFlight
        }

        var remaining: [QueuedMutation] = []

        for var mutation in pendingMutations {
            do {
                try await apiClient.executeRawMutation(
                    endpoint: mutation.endpoint,
                    method: mutation.method,
                    payloadJson: mutation.payloadJson
                )
                // Successfully synchronized
            } catch {
                mutation.retryCount += 1
                if mutation.retryCount > 5 {
                    mutation.status = .conflict
                } else {
                    mutation.status = .failed
                }
                remaining.append(mutation)
            }
        }

        let updatedRemaining = remaining
        await MainActor.run {
            self.pendingMutations = updatedRemaining
            self.lastSyncDate = Date()
            self.currentSyncStatus = updatedRemaining.isEmpty ? .synced : .pending
            self.persistQueue()
        }
    }

    private func persistQueue() {
        OfflineDataStore.shared.save(pendingMutations, filename: storeKey)
    }

    private func loadPersistedQueue() {
        if let loaded = OfflineDataStore.shared.load(filename: storeKey, type: [QueuedMutation].self) {
            self.pendingMutations = loaded
            self.currentSyncStatus = loaded.isEmpty ? .synced : .pending
        }
    }
}

