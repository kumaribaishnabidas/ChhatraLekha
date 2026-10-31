import SwiftUI

/// Banner displaying real-time offline status and unsynced pending changes.
public struct StatusBanner: View {
    @ObservedObject var networkMonitor = NetworkMonitor.shared
    @ObservedObject var syncQueue = SyncQueue.shared

    public init() {}

    public var body: some View {
        VStack(spacing: 0) {
            if !networkMonitor.isConnected {
                HStack(spacing: 8) {
                    Image(systemName: "wifi.slash")
                        .font(.caption.bold())
                    Text("Offline Mode - Cached records available locally")
                        .font(.caption.weight(.medium))
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.warningAmber.opacity(0.15))
                .foregroundColor(.warningAmber)
            } else if syncQueue.pendingMutations.count > 0 {
                HStack(spacing: 8) {
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .font(.caption.bold())
                    Text("\(syncQueue.pendingMutations.count) changes pending sync")
                        .font(.caption.weight(.medium))
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.brandPrimary.opacity(0.12))
                .foregroundColor(.brandPrimary)
            }
        }
    }
}

