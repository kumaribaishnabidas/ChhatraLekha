import Foundation
import Combine

/// Manages institution administrator oversight, compliance quotas, and student register.
@MainActor
public final class AdminViewModel: ObservableObject {
    @Published public var totalSanctionedIntake: Int = 180
    @Published public var totalEnrolled: Int = 168
    @Published public var detectedAnomaliesCount: Int = 0
    @Published public var studentRegister: [StudentProfile] = []
    @Published public var isLoading: Bool = false

    public init() {
        loadRegister()
    }

    public func loadRegister() {
        isLoading = true
        self.studentRegister = [
            StudentProfile(id: "std_001", apaarId: "984210357890", fullName: "Aarav Sharma", rollNumber: "2024-CS-042", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024),
            StudentProfile(id: "std_002", apaarId: "984210357891", fullName: "Bhavna Patel", rollNumber: "2024-CS-043", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024),
            StudentProfile(id: "std_003", apaarId: "984210357892", fullName: "Chirag Sen", rollNumber: "2024-CS-044", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024),
            StudentProfile(id: "std_004", apaarId: "984210357893", fullName: "Divya Nambiar", rollNumber: "2024-CS-045", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024),
            StudentProfile(id: "std_005", apaarId: "984210357894", fullName: "Ehsan Qureshi", rollNumber: "2024-CS-046", institutionId: "inst_101", institutionName: "Delhi Public College", program: "CSE", gradeOrYear: "Sem IV", section: "A", enrollmentYear: 2024)
        ]
        self.isLoading = false
    }
}

