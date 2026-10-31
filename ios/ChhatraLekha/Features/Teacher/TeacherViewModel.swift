import Foundation
import Combine

/// Manages teacher workflows: class roster, attendance marking, and grading.
@MainActor
public final class TeacherViewModel: ObservableObject {
    @Published public var assignedClasses: [String] = ["CSE - Semester IV (Section A)", "CSE - Semester VI (Section B)"]
    @Published public var selectedClass: String = "CSE - Semester IV (Section A)"
    @Published public var studentRoster: [StudentProfile] = []
    @Published public var attendanceDraft: [String: String] = [:]
    @Published public var isSubmitting: Bool = false
    @Published public var submissionSuccess: Bool = false
    @Published public var errorMessage: String?

    public init() {
        loadClassRoster()
    }

    public func loadClassRoster() {
        let students = [
            StudentProfile(id: "std_001", apaarId: "984210357890", fullName: "Aarav Sharma", rollNumber: "2024-CS-042", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024),
            StudentProfile(id: "std_002", apaarId: "984210357891", fullName: "Bhavna Patel", rollNumber: "2024-CS-043", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024),
            StudentProfile(id: "std_003", apaarId: "984210357892", fullName: "Chirag Sen", rollNumber: "2024-CS-044", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024),
            StudentProfile(id: "std_004", apaarId: "984210357893", fullName: "Divya Nambiar", rollNumber: "2024-CS-045", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024),
            StudentProfile(id: "std_005", apaarId: "984210357894", fullName: "Ehsan Qureshi", rollNumber: "2024-CS-046", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024)
        ]

        self.studentRoster = students
        // Default all to PRESENT
        var draft: [String: String] = [:]
        for s in students {
            draft[s.id] = "PRESENT"
        }
        self.attendanceDraft = draft
    }

    public func toggleAttendance(for studentId: String) {
        let current = attendanceDraft[studentId] ?? "PRESENT"
        attendanceDraft[studentId] = (current == "PRESENT") ? "ABSENT" : "PRESENT"
    }

    public func submitAttendance(sessionName: String = "Operating Systems") async {
        isSubmitting = true
        submissionSuccess = false
        errorMessage = nil

        let payload: [String: Any] = [
            "class": selectedClass,
            "session": sessionName,
            "date": ISO8601DateFormatter().string(from: Date()),
            "records": attendanceDraft
        ]

        if let jsonData = try? JSONSerialization.data(withJSONObject: payload),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            if NetworkMonitor.shared.isConnected {
                do {
                    try await ApiClient.shared.executeRawMutation(
                        endpoint: "/api/attendance/record",
                        method: "POST",
                        payloadJson: jsonString
                    )
                    submissionSuccess = true
                } catch {
                    // Queue for offline synchronization
                    SyncQueue.shared.enqueue(endpoint: "/api/attendance/record", method: "POST", payloadJson: jsonString)
                    submissionSuccess = true
                }
            } else {
                SyncQueue.shared.enqueue(endpoint: "/api/attendance/record", method: "POST", payloadJson: jsonString)
                submissionSuccess = true
            }
        }
        isSubmitting = false
    }
}

