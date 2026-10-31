import Foundation
import Combine

/// Manages student academic data, wallet credentials, attendance, and exam scores.
@MainActor
public final class StudentViewModel: ObservableObject {
    @Published public var studentProfile: StudentProfile?
    @Published public var credentials: [AcademicCredential] = []
    @Published public var attendanceHistory: [AttendanceRecord] = []
    @Published public var assessmentResults: [AssessmentResult] = []
    @Published public var announcements: [AnnouncementItem] = []
    @Published public var isLoading: Bool = false
    @Published public var errorMessage: String?
    @Published public var activeShareToken: String?

    private let apiClient: ApiClient

    public init(apiClient: ApiClient = .shared) {
        self.apiClient = apiClient
        loadStudentData()
    }

    public func loadStudentData() {
        isLoading = true
        errorMessage = nil

        // Synthetic reference profile seeded for offline-first reliability
        let defaultProfile = StudentProfile(
            id: "std_001",
            apaarId: "984210357890",
            fullName: "Aarav Sharma",
            rollNumber: "2024-CS-042",
            institutionId: "inst_101",
            institutionName: "Delhi Public College of Engineering",
            program: "Computer Science & Engineering",
            gradeOrYear: "Semester IV",
            section: "A",
            enrollmentYear: 2024,
            status: "ACTIVE",
            guardianName: "Sunita Sharma",
            guardianContact: "+91 98765 43210",
            attendancePercentage: 94.2,
            cgpaOrPercentage: 8.85
        )

        let sampleCredentials = [
            AcademicCredential(
                id: "cred_01",
                title: "Semester III Grade Transcript",
                credentialType: "TRANSCRIPT",
                issuingInstitution: "Delhi Public College of Engineering",
                issueDate: "15 Jan 2026",
                verificationToken: "tok_s3_8f9a2b1c4e",
                sealHash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            ),
            AcademicCredential(
                id: "cred_02",
                title: "Bonafide Student Certificate",
                credentialType: "BONAFIDE",
                issuingInstitution: "Delhi Public College of Engineering",
                issueDate: "02 Feb 2026",
                verificationToken: "tok_bonafide_99d12a",
                sealHash: "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
            )
        ]

        let sampleAttendance = [
            AttendanceRecord(date: "31 Oct 2026", courseOrSubject: "Data Structures & Algorithms", status: "PRESENT"),
            AttendanceRecord(date: "30 Oct 2026", courseOrSubject: "Database Management Systems", status: "PRESENT"),
            AttendanceRecord(date: "29 Oct 2026", courseOrSubject: "Operating Systems", status: "PRESENT"),
            AttendanceRecord(date: "28 Oct 2026", courseOrSubject: "Computer Networks", status: "ABSENT", remarks: "Medical leave approved"),
            AttendanceRecord(date: "27 Oct 2026", courseOrSubject: "Discrete Mathematics", status: "PRESENT")
        ]

        let sampleResults = [
            AssessmentResult(term: "Mid-Term Exam", subjectName: "Data Structures", scoreObtained: 46.0, maxScore: 50.0, grade: "A+"),
            AssessmentResult(term: "Mid-Term Exam", subjectName: "Database Systems", scoreObtained: 43.5, maxScore: 50.0, grade: "A"),
            AssessmentResult(term: "Mid-Term Exam", subjectName: "Operating Systems", scoreObtained: 48.0, maxScore: 50.0, grade: "O"),
            AssessmentResult(term: "Mid-Term Exam", subjectName: "Computer Networks", scoreObtained: 41.0, maxScore: 50.0, grade: "A")
        ]

        let sampleAnnouncements = [
            AnnouncementItem(
                title: "End-Term Practical Examination Schedule",
                content: "Practical laboratory assessments will commence on 18 November 2026. Hall tickets available in academic wallet.",
                datePublished: "28 Oct 2026",
                authorRole: "Controller of Examinations",
                priority: "HIGH"
            ),
            AnnouncementItem(
                title: "Annual Sports & Technical Symposium Registration",
                content: "Submit department team nominations before 10 November 2026 via respective faculty mentors.",
                datePublished: "24 Oct 2026",
                authorRole: "Student Affairs Office",
                priority: "NORMAL"
            )
        ]

        // Load cached or fall back to synthetic baseline
        if let cachedProfile: StudentProfile = OfflineDataStore.shared.load(filename: "student_profile.json", type: StudentProfile.self) {
            self.studentProfile = cachedProfile
        } else {
            self.studentProfile = defaultProfile
            OfflineDataStore.shared.save(defaultProfile, filename: "student_profile.json")
        }

        self.credentials = sampleCredentials
        self.attendanceHistory = sampleAttendance
        self.assessmentResults = sampleResults
        self.announcements = sampleAnnouncements
        self.isLoading = false
    }

    public func issueShareToken(for credential: AcademicCredential) {
        self.activeShareToken = credential.verificationToken
    }
}

