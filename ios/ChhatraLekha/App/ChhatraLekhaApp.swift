import SwiftUI

@main
struct ChhatraLekhaApp: App {
    @StateObject private var authViewModel = AuthViewModel()
    @StateObject private var networkMonitor = NetworkMonitor.shared
    @StateObject private var syncQueue = SyncQueue.shared

    var body: some Scene {
        WindowGroup {
            Group {
                if authViewModel.isAuthenticated {
                    MainTabView(authViewModel: authViewModel)
                } else {
                    LoginView(viewModel: authViewModel)
                }
            }
            .tint(Color.brandPrimary)
            .task {
                // Background check for pending mutations if online
                if networkMonitor.isConnected && !syncQueue.pendingMutations.isEmpty {
                    await syncQueue.processQueue(apiClient: .shared)
                }
            }
        }
    }
}

