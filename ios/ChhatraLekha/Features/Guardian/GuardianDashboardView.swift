import SwiftUI

/// Parent and guardian dashboard for reviewing linked student performance and notices.
public struct GuardianDashboardView: View {
    @ObservedObject var viewModel: GuardianViewModel

    public init(viewModel: GuardianViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    StatusBanner()

                    if let student = viewModel.selectedStudent {
                        // Ward Overview Card
                        VStack(alignment: .leading, spacing: 10) {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Linked Ward")
                                        .font(.caption.bold())
                                        .foregroundColor(.white.opacity(0.8))
                                        .textCase(.uppercase)
                                    Text(student.fullName)
                                        .font(.title2.bold())
                                        .foregroundColor(.white)
                                }
                                Spacer()
                                Image(systemName: "person.2.circle.fill")
                                    .font(.system(size: 36))
                                    .foregroundColor(.white.opacity(0.9))
                            }

                            Text("\(student.program) · \(student.gradeOrYear)")
                                .font(.subheadline)
                                .foregroundColor(.white.opacity(0.9))

                            Divider().background(Color.white.opacity(0.2))

                            HStack {
                                Text("Roll: \(student.rollNumber)")
                                    .font(.caption.bold())
                                    .foregroundColor(.white)
                                Spacer()
                                Text("APAAR: \(student.maskedApaarId)")
                                    .font(.caption.monospaced())
                                    .foregroundColor(.white.opacity(0.8))
                            }
                        }
                        .padding(18)
                        .background(
                            LinearGradient(
                                colors: [Color.brandDeep, Color.successGreen.opacity(0.85)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .cornerRadius(14)
                        .padding(.horizontal, 16)

                        // Vital Indicators
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                            StatCard(
                                title: "Ward Attendance",
                                value: String(format: "%.1f%%", student.attendancePercentage),
                                subtitle: "Above 75% Target",
                                iconName: "checkmark.circle.fill",
                                iconColor: .successGreen
                            )
                            StatCard(
                                title: "Recent Standing",
                                value: String(format: "%.2f CGPA", student.cgpaOrPercentage),
                                subtitle: "First Class Standing",
                                iconName: "star.fill",
                                iconColor: .warningAmber
                            )
                        }
                        .padding(.horizontal, 16)

                        // Recent Attendance History
                        VStack(alignment: .leading, spacing: 10) {
                            Text("Recent Attendance Logs")
                                .font(.headline)
                                .padding(.horizontal, 16)

                            ForEach(viewModel.attendanceOverview) { rec in
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(rec.courseOrSubject)
                                            .font(.subheadline.bold())
                                            .foregroundColor(.inkPrimary)
                                        Text(rec.date)
                                            .font(.caption)
                                            .foregroundColor(.inkMuted)
                                    }
                                    Spacer()
                                    Text(rec.status)
                                        .font(.caption.bold())
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(rec.status == "PRESENT" ? Color.successGreen.opacity(0.15) : Color.errorCrimson.opacity(0.15))
                                        .foregroundColor(rec.status == "PRESENT" ? .successGreen : .errorCrimson)
                                        .cornerRadius(6)
                                }
                                .padding(12)
                                .background(Color.surfaceBackground)
                                .cornerRadius(10)
                                .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.borderLine, lineWidth: 1))
                                .padding(.horizontal, 16)
                            }
                        }

                        // School Notices
                        VStack(alignment: .leading, spacing: 10) {
                            Text("School Notices for Guardians")
                                .font(.headline)
                                .padding(.horizontal, 16)

                            ForEach(viewModel.announcements) { notice in
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(notice.title)
                                        .font(.subheadline.bold())
                                    Text(notice.content)
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                    Text(notice.datePublished)
                                        .font(.caption2)
                                        .foregroundColor(.brandPrimary)
                                }
                                .padding(12)
                                .background(Color.surfaceBackground)
                                .cornerRadius(10)
                                .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.borderLine, lineWidth: 1))
                                .padding(.horizontal, 16)
                            }
                        }
                    } else {
                        EmptyStateView(
                            title: "No Linked Students",
                            message: "Please contact the institution administrator to associate your guardian phone number with your ward's student record.",
                            iconName: "person.crop.circle.badge.plus"
                        )
                    }
                }
                .padding(.vertical, 12)
            }
            .navigationTitle("Guardian Portal")
        }
    }
}

