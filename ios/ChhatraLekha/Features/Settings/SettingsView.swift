import SwiftUI

/// Settings, privacy controls, sync management, and account options.
public struct SettingsView: View {
    @ObservedObject var authViewModel: AuthViewModel
    @ObservedObject var syncQueue = SyncQueue.shared
    @State private var showingDeleteAlert = false
    @State private var biometricToggle: Bool = false

    public init(authViewModel: AuthViewModel) {
        self.authViewModel = authViewModel
    }

    public var body: some View {
        NavigationStack {
            List {
                Section(header: Text("Account & Role")) {
                    HStack {
                        Image(systemName: authViewModel.selectedRole.iconName)
                            .foregroundColor(.brandPrimary)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(authViewModel.selectedRole.displayName)
                                .font(.subheadline.bold())
                            Text(authViewModel.selectedRole.subtitle)
                                .font(.caption2)
                                .foregroundColor(.inkMuted)
                        }
                    }
                    .padding(.vertical, 4)
                }

                Section(header: Text("Security & Storage")) {
                    if BiometricManager.shared.biometricType != .none {
                        Toggle(isOn: $biometricToggle) {
                            HStack {
                                Image(systemName: "faceid")
                                    .foregroundColor(.brandPrimary)
                                Text("Biometric Unlock")
                            }
                        }
                    }

                    HStack {
                        Image(systemName: "arrow.triangle.2.circlepath")
                            .foregroundColor(.brandPrimary)
                        Text("Pending Sync Changes")
                        Spacer()
                        Text("\(syncQueue.pendingMutations.count)")
                            .font(.subheadline.bold())
                            .foregroundColor(syncQueue.pendingMutations.isEmpty ? .inkMuted : .warningAmber)
                    }

                    Button(action: {
                        Task {
                            await syncQueue.processQueue(apiClient: .shared)
                        }
                    }) {
                        Text("Force Synchronize Now")
                            .font(.subheadline.bold())
                            .foregroundColor(.brandPrimary)
                    }
                    .disabled(syncQueue.pendingMutations.isEmpty)
                }

                Section(header: Text("Privacy & Governance")) {
                    Link(destination: URL(string: "https://chhatralekha.vercel.app/privacy")!) {
                        HStack {
                            Image(systemName: "hand.raised.fill")
                                .foregroundColor(.brandPrimary)
                            Text("Privacy Policy (DPDP Act 2023)")
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .font(.caption)
                                .foregroundColor(.inkMuted)
                        }
                    }

                    Link(destination: URL(string: "https://chhatralekha.vercel.app/terms")!) {
                        HStack {
                            Image(systemName: "doc.text.fill")
                                .foregroundColor(.brandPrimary)
                            Text("Terms of Service")
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .font(.caption)
                                .foregroundColor(.inkMuted)
                        }
                    }

                    Link(destination: URL(string: "https://chhatralekha.vercel.app/transparency")!) {
                        HStack {
                            Image(systemName: "chart.bar.doc.horizontal.fill")
                                .foregroundColor(.brandPrimary)
                            Text("Transparency Charter")
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .font(.caption)
                                .foregroundColor(.inkMuted)
                        }
                    }

                    HStack {
                        Image(systemName: "envelope.fill")
                            .foregroundColor(.brandPrimary)
                        Text("Data Protection Desk")
                        Spacer()
                        Text("grievance@chhatralekha.in")
                            .font(.caption.monospaced())
                            .foregroundColor(.inkMuted)
                    }
                }

                Section(header: Text("Session Actions")) {
                    Button(action: { authViewModel.logout() }) {
                        HStack {
                            Image(systemName: "rectangle.portrait.and.arrow.right")
                            Text("Sign Out")
                        }
                        .foregroundColor(.errorCrimson)
                    }

                    Button(action: { showingDeleteAlert = true }) {
                        HStack {
                            Image(systemName: "trash")
                            Text("Request Account Deletion")
                        }
                        .foregroundColor(.errorCrimson)
                    }
                }
            }
            .navigationTitle("App Settings")
            .alert("Request Account Deletion", isPresented: $showingDeleteAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Submit Request", role: .destructive) {
                    authViewModel.logout()
                }
            } message: {
                Text("Your request will be submitted to your institution's grievance officer in compliance with Section 12 of the DPDP Act 2023. All local caches will be cleared.")
            }
        }
    }
}

