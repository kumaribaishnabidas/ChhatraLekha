import SwiftUI

/// Detailed attendance register screen for students and families.
public struct AttendanceView: View {
    @ObservedObject var viewModel: StudentViewModel

    public init(viewModel: StudentViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            List {
                Section(header: Text("Summary Overview")) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Current Attendance")
                                .font(.caption.bold())
                                .foregroundColor(.inkMuted)
                            Text(String(format: "%.1f%%", viewModel.studentProfile?.attendancePercentage ?? 0.0))
                                .font(.system(size: 32, weight: .black))
                                .foregroundColor(
                                    (viewModel.studentProfile?.attendancePercentage ?? 0.0) >= 75.0 ? .successGreen : .warningAmber
                                )
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 4) {
                            Text("Regulatory Threshold")
                                .font(.caption)
                                .foregroundColor(.inkMuted)
                            Text("75.0% Required")
                                .font(.footnote.bold())
                                .foregroundColor(.brandPrimary)
                        }
                    }
                    .padding(.vertical, 8)
                }

                Section(header: Text("Session Records")) {
                    ForEach(viewModel.attendanceHistory) { record in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(record.courseOrSubject)
                                    .font(.subheadline.bold())
                                    .foregroundColor(.inkPrimary)
                                Text(record.date)
                                    .font(.caption)
                                    .foregroundColor(.inkMuted)
                                if let remarks = record.remarks {
                                    Text(remarks)
                                        .font(.caption2)
                                        .foregroundColor(.inkMuted)
                                }
                            }
                            Spacer()
                            Text(record.status)
                                .font(.caption.bold())
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    record.status == "PRESENT"
                                    ? Color.successGreen.opacity(0.15)
                                    : Color.errorCrimson.opacity(0.15)
                                )
                                .foregroundColor(
                                    record.status == "PRESENT" ? .successGreen : .errorCrimson
                                )
                                .cornerRadius(6)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
            .navigationTitle("Attendance Register")
        }
    }
}

/// Academic examination and assessment marks review.
public struct ResultsView: View {
    @ObservedObject var viewModel: StudentViewModel

    public init(viewModel: StudentViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            List {
                Section(header: Text("Academic Standing")) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Cumulative CGPA")
                                .font(.caption.bold())
                                .foregroundColor(.inkMuted)
                            Text(String(format: "%.2f", viewModel.studentProfile?.cgpaOrPercentage ?? 0.0))
                                .font(.system(size: 32, weight: .black))
                                .foregroundColor(.brandPrimary)
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 4) {
                            Text("Classification")
                                .font(.caption)
                                .foregroundColor(.inkMuted)
                            Text("First Class with Distinction")
                                .font(.footnote.bold())
                                .foregroundColor(.successGreen)
                        }
                    }
                    .padding(.vertical, 8)
                }

                Section(header: Text("Assessment Performance")) {
                    ForEach(viewModel.assessmentResults) { res in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(res.subjectName)
                                    .font(.subheadline.bold())
                                    .foregroundColor(.inkPrimary)
                                Text(res.term)
                                    .font(.caption)
                                    .foregroundColor(.inkMuted)
                            }
                            Spacer()
                            VStack(alignment: .trailing, spacing: 2) {
                                Text(String(format: "%.1f / %.1f", res.scoreObtained, res.maxScore))
                                    .font(.footnote.bold())
                                    .foregroundColor(.inkPrimary)
                                Text("Grade: \(res.grade)")
                                    .font(.caption.bold())
                                    .foregroundColor(.brandPrimary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
            .navigationTitle("Academic Results")
        }
    }
}

