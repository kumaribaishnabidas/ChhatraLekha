import SwiftUI

/// Primary home screen for the student portal.
public struct StudentDashboardView: View {
    @ObservedObject var viewModel: StudentViewModel
    @State private var showingWallet = false

    public init(viewModel: StudentViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    StatusBanner()

                    if let profile = viewModel.studentProfile {
                        // Student Identity Header Card
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(profile.fullName)
                                        .font(.title2.bold())
                                        .foregroundColor(.white)
                                    Text(profile.institutionName)
                                        .font(.subheadline)
                                        .foregroundColor(.white.opacity(0.85))
                                }
                                Spacer()
                                Image(systemName: "person.crop.circle.badge.checkmark")
                                    .font(.system(size: 38))
                                    .foregroundColor(.white.opacity(0.9))
                            }

                            Divider().background(Color.white.opacity(0.2))

                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("APAAR ID")
                                        .font(.caption2.bold())
                                        .foregroundColor(.white.opacity(0.7))
                                    Text(profile.maskedApaarId)
                                        .font(.footnote.monospaced())
                                        .fontWeight(.semibold)
                                        .foregroundColor(.white)
                                }
                                Spacer()
                                VStack(alignment: .trailing, spacing: 2) {
                                    Text("Roll Number")
                                        .font(.caption2.bold())
                                        .foregroundColor(.white.opacity(0.7))
                                    Text(profile.rollNumber)
                                        .font(.footnote)
                                        .fontWeight(.semibold)
                                        .foregroundColor(.white)
                                }
                            }
                        }
                        .padding(18)
                        .background(
                            LinearGradient(
                                colors: [Color.brandDeep, Color.brandPrimary],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .cornerRadius(14)
                        .padding(.horizontal, 16)

                        // Metric Stat Cards Grid
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                            StatCard(
                                title: "Attendance",
                                value: String(format: "%.1f%%", profile.attendancePercentage),
                                subtitle: "Current Semester",
                                iconName: "calendar.badge.clock",
                                iconColor: profile.attendancePercentage >= 75.0 ? .successGreen : .warningAmber
                            )
                            StatCard(
                                title: "Performance",
                                value: String(format: "%.2f", profile.cgpaOrPercentage),
                                subtitle: "Cumulative CGPA",
                                iconName: "chart.line.uptrend.xyaxis",
                                iconColor: .brandPrimary
                            )
                            StatCard(
                                title: "Program",
                                value: profile.gradeOrYear,
                                subtitle: profile.program,
                                iconName: "book.closed",
                                iconColor: .brandPrimary
                            )
                            StatCard(
                                title: "Credentials",
                                value: "\(viewModel.credentials.count) Issued",
                                subtitle: "Verified Seals",
                                iconName: "checkmark.seal.fill",
                                iconColor: .successGreen
                            )
                        }
                        .padding(.horizontal, 16)

                        // Quick Action: Academic Wallet
                        Button(action: { showingWallet = true }) {
                            HStack {
                                Image(systemName: "wallet.pass.fill")
                                    .font(.title3)
                                    .foregroundColor(.saffronAccent)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Academic Identity Wallet & QR")
                                        .font(.subheadline.bold())
                                        .foregroundColor(.inkPrimary)
                                    Text("Generate private verification badges and degree seals")
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.caption)
                                    .foregroundColor(.inkMuted)
                            }
                            .padding(14)
                            .background(Color.surfaceBackground)
                            .cornerRadius(10)
                            .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.borderLine, lineWidth: 1))
                        }
                        .padding(.horizontal, 16)

                        // Campus Announcements
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Official Announcements")
                                .font(.headline)
                                .padding(.horizontal, 16)

                            ForEach(viewModel.announcements) { notice in
                                VStack(alignment: .leading, spacing: 6) {
                                    HStack {
                                        Text(notice.title)
                                            .font(.subheadline.bold())
                                            .foregroundColor(.inkPrimary)
                                        Spacer()
                                        if notice.priority == "HIGH" {
                                            Text("Important")
                                                .font(.caption2.bold())
                                                .padding(.horizontal, 6)
                                                .padding(.vertical, 2)
                                                .background(Color.warningAmber.opacity(0.15))
                                                .foregroundColor(.warningAmber)
                                                .cornerRadius(4)
                                        }
                                    }
                                    Text(notice.content)
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                    HStack {
                                        Text(notice.authorRole)
                                            .font(.caption2)
                                            .foregroundColor(.brandPrimary)
                                        Spacer()
                                        Text(notice.datePublished)
                                            .font(.caption2)
                                            .foregroundColor(.inkMuted)
                                    }
                                }
                                .padding(14)
                                .background(Color.surfaceBackground)
                                .cornerRadius(10)
                                .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.borderLine, lineWidth: 1))
                                .padding(.horizontal, 16)
                            }
                        }
                    } else {
                        EmptyStateView(
                            title: "Loading Academic Profile",
                            message: "Connecting to secure institutional registers...",
                            iconName: "person.crop.circle"
                        )
                    }
                }
                .padding(.vertical, 12)
            }
            .navigationTitle("Student Workspace")
            .sheet(isPresented: $showingWallet) {
                AcademicWalletView(viewModel: viewModel)
            }
        }
    }
}

