import SwiftUI

/// Institution administrator overview and management screen.
public struct AdminDashboardView: View {
    @ObservedObject var viewModel: AdminViewModel

    public init(viewModel: AdminViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    StatusBanner()

                    // Institution Header Card
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Institutional Administration")
                            .font(.caption.bold())
                            .foregroundColor(.white.opacity(0.8))
                            .textCase(.uppercase)
                        Text("Delhi Public College of Engineering")
                            .font(.title2.bold())
                            .foregroundColor(.white)
                        Text("Permanent Affiliation · AICTE / State Education Directorate")
                            .font(.subheadline)
                            .foregroundColor(.white.opacity(0.85))
                    }
                    .padding(18)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(
                        LinearGradient(
                            colors: [Color.brandDeep, Color.brandPrimary],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .cornerRadius(14)
                    .padding(.horizontal, 16)

                    // Operational Intake Metrics
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        StatCard(
                            title: "Sanctioned Intake",
                            value: "\(viewModel.totalSanctionedIntake)",
                            subtitle: "Academic Year 2026",
                            iconName: "chart.bar.xaxis",
                            iconColor: .brandPrimary
                        )
                        StatCard(
                            title: "Total Enrolled",
                            value: "\(viewModel.totalEnrolled)",
                            subtitle: "93.3% Quota Filled",
                            iconName: "person.3.fill",
                            iconColor: .successGreen
                        )
                        StatCard(
                            title: "Detected Anomalies",
                            value: "\(viewModel.detectedAnomaliesCount)",
                            subtitle: "Zero Regulatory Breaches",
                            iconName: "checkmark.shield.fill",
                            iconColor: .successGreen
                        )
                        StatCard(
                            title: "Audit Chain",
                            value: "Intact",
                            subtitle: "Tamper-Evident SHA-256",
                            iconName: "lock.shield.fill",
                            iconColor: .brandPrimary
                        )
                    }
                    .padding(.horizontal, 16)

                    // Enrolled Students Register
                    VStack(alignment: .leading, spacing: 10) {
                        HStack {
                            Text("Enrolled Student Register")
                                .font(.headline)
                            Spacer()
                            Text("\(viewModel.studentRegister.count) Records")
                                .font(.caption.bold())
                                .foregroundColor(.inkMuted)
                        }
                        .padding(.horizontal, 16)

                        ForEach(viewModel.studentRegister) { s in
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text(s.fullName)
                                        .font(.subheadline.bold())
                                    Spacer()
                                    Text(s.rollNumber)
                                        .font(.caption.bold())
                                        .foregroundColor(.brandPrimary)
                                }
                                HStack {
                                    Text("APAAR: \(s.maskedApaarId)")
                                        .font(.caption2.monospaced())
                                        .foregroundColor(.inkMuted)
                                    Spacer()
                                    Text("\(s.program) · \(s.gradeOrYear)")
                                        .font(.caption2)
                                        .foregroundColor(.inkMuted)
                                }
                            }
                            .padding(12)
                            .background(Color.surfaceBackground)
                            .cornerRadius(10)
                            .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.borderLine, lineWidth: 1))
                            .padding(.horizontal, 16)
                        }
                    }
                }
                .padding(.vertical, 12)
            }
            .navigationTitle("Admin Portal")
        }
    }
}

