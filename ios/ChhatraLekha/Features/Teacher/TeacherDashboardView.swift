import SwiftUI

/// Faculty workspace dashboard.
public struct TeacherDashboardView: View {
    @ObservedObject var viewModel: TeacherViewModel
    @State private var showingMarkingSheet = false

    public init(viewModel: TeacherViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    StatusBanner()

                    // Faculty Profile Banner
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Faculty Workspace")
                            .font(.caption.bold())
                            .foregroundColor(.white.opacity(0.8))
                            .textCase(.uppercase)
                        Text("Department of Computer Science")
                            .font(.title2.bold())
                            .foregroundColor(.white)
                        Text("Assigned to 2 Active Cohorts · 68 Enrolled Students")
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

                    // Quick Actions
                    VStack(spacing: 12) {
                        Button(action: { showingMarkingSheet = true }) {
                            HStack {
                                Image(systemName: "checkmark.circle.badge.questionmark")
                                    .font(.title2)
                                    .foregroundColor(.brandPrimary)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Mark Today's Attendance")
                                        .font(.subheadline.bold())
                                        .foregroundColor(.inkPrimary)
                                    Text("Record session presence for \(viewModel.selectedClass)")
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
                    }
                    .padding(.horizontal, 16)

                    // Class Roster
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Current Class Cohort")
                            .font(.headline)
                            .padding(.horizontal, 16)

                        ForEach(viewModel.studentRoster) { std in
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(std.fullName)
                                        .font(.subheadline.bold())
                                        .foregroundColor(.inkPrimary)
                                    Text("Roll: \(std.rollNumber) · \(std.maskedApaarId)")
                                        .font(.caption.monospaced())
                                        .foregroundColor(.inkMuted)
                                }
                                Spacer()
                                Text(std.status)
                                    .font(.caption2.bold())
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.successGreen.opacity(0.12))
                                    .foregroundColor(.successGreen)
                                    .cornerRadius(4)
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
            .navigationTitle("Faculty Portal")
            .sheet(isPresented: $showingMarkingSheet) {
                AttendanceMarkingView(viewModel: viewModel)
            }
        }
    }
}

/// Dedicated attendance marking roll-call view with offline queue integration.
public struct AttendanceMarkingView: View {
    @ObservedObject var viewModel: TeacherViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var sessionTitle = "Operating Systems Lab"

    public var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Session Name")
                        .font(.caption.bold())
                        .foregroundColor(.inkMuted)
                    TextField("Session or subject title", text: $sessionTitle)
                        .padding(10)
                        .background(Color.surfaceBackground)
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.borderLine, lineWidth: 1))
                }
                .padding(.horizontal, 16)
                .padding(.top, 12)

                List {
                    Section(header: Text("Tap Student to Toggle Status")) {
                        ForEach(viewModel.studentRoster) { s in
                            let status = viewModel.attendanceDraft[s.id] ?? "PRESENT"
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(s.fullName)
                                        .font(.subheadline.bold())
                                    Text("Roll: \(s.rollNumber)")
                                        .font(.caption)
                                        .foregroundColor(.inkMuted)
                                }
                                Spacer()
                                Button(action: { viewModel.toggleAttendance(for: s.id) }) {
                                    Text(status)
                                        .font(.caption.bold())
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(status == "PRESENT" ? Color.successGreen : Color.errorCrimson)
                                        .foregroundColor(.white)
                                        .cornerRadius(6)
                                }
                                .buttonStyle(BorderlessButtonStyle())
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }

                if viewModel.submissionSuccess {
                    Text("Attendance successfully recorded and queued.")
                        .font(.caption.bold())
                        .foregroundColor(.successGreen)
                        .padding(.horizontal, 16)
                }

                PrimaryButton(
                    title: "Submit Attendance Session",
                    iconName: "checkmark",
                    isLoading: viewModel.isSubmitting
                ) {
                    Task {
                        await viewModel.submitAttendance(sessionName: sessionTitle)
                        try? await Task.sleep(nanoseconds: 800_000_000)
                        dismiss()
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 12)
            }
            .navigationTitle("Mark Attendance")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
    }
}

