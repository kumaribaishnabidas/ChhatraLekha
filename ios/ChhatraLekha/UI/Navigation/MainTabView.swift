import SwiftUI

/// Role-aware main tab container providing persona-tailored navigation hierarchies.
public struct MainTabView: View {
    @ObservedObject var authViewModel: AuthViewModel
    @StateObject private var studentViewModel = StudentViewModel()
    @StateObject private var guardianViewModel = GuardianViewModel()
    @StateObject private var teacherViewModel = TeacherViewModel()
    @StateObject private var adminViewModel = AdminViewModel()
    @StateObject private var verifierViewModel = VerifierViewModel()

    public init(authViewModel: AuthViewModel) {
        self.authViewModel = authViewModel
    }

    public var body: some View {
        TabView {
            switch authViewModel.selectedRole {
            case .student:
                StudentDashboardView(viewModel: studentViewModel)
                    .tabItem {
                        Label("Home", systemImage: "house.fill")
                    }
                AttendanceView(viewModel: studentViewModel)
                    .tabItem {
                        Label("Attendance", systemImage: "calendar.badge.clock")
                    }
                ResultsView(viewModel: studentViewModel)
                    .tabItem {
                        Label("Results", systemImage: "chart.line.uptrend.xyaxis")
                    }
                AcademicWalletView(viewModel: studentViewModel)
                    .tabItem {
                        Label("Wallet", systemImage: "wallet.pass.fill")
                    }
                SettingsView(authViewModel: authViewModel)
                    .tabItem {
                        Label("Settings", systemImage: "gearshape.fill")
                    }

            case .parent:
                GuardianDashboardView(viewModel: guardianViewModel)
                    .tabItem {
                        Label("Ward Overview", systemImage: "person.2.fill")
                    }
                AttendanceView(viewModel: studentViewModel)
                    .tabItem {
                        Label("Attendance", systemImage: "calendar.badge.clock")
                    }
                ResultsView(viewModel: studentViewModel)
                    .tabItem {
                        Label("Results", systemImage: "chart.line.uptrend.xyaxis")
                    }
                SettingsView(authViewModel: authViewModel)
                    .tabItem {
                        Label("Settings", systemImage: "gearshape.fill")
                    }

            case .teacher:
                TeacherDashboardView(viewModel: teacherViewModel)
                    .tabItem {
                        Label("Classes", systemImage: "person.3.fill")
                    }
                AttendanceMarkingView(viewModel: teacherViewModel)
                    .tabItem {
                        Label("Mark Roll", systemImage: "checkmark.circle.fill")
                    }
                SettingsView(authViewModel: authViewModel)
                    .tabItem {
                        Label("Settings", systemImage: "gearshape.fill")
                    }

            case .institution, .national:
                AdminDashboardView(viewModel: adminViewModel)
                    .tabItem {
                        Label("Dashboard", systemImage: "chart.bar.fill")
                    }
                VerifierView(viewModel: verifierViewModel)
                    .tabItem {
                        Label("Verify", systemImage: "qrcode.viewfinder")
                    }
                SettingsView(authViewModel: authViewModel)
                    .tabItem {
                        Label("Settings", systemImage: "gearshape.fill")
                    }

            case .verifier:
                VerifierView(viewModel: verifierViewModel)
                    .tabItem {
                        Label("Verify Token", systemImage: "qrcode.viewfinder")
                    }
                SettingsView(authViewModel: authViewModel)
                    .tabItem {
                        Label("Settings", systemImage: "gearshape.fill")
                    }
            }
        }
    }
}

