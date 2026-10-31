import Foundation
import Combine

/// Manages parent/guardian portal view for explicitly linked student records.
@MainActor
public final class GuardianViewModel: ObservableObject {
    @Published public var linkedStudents: [StudentProfile] = []
    @Published public var selectedStudent: StudentProfile?
    @Published public var attendanceOverview: [AttendanceRecord] = []
    @Published public var recentResults: [AssessmentResult] = []
    @Published public var announcements: [AnnouncementItem] = []
    @Published public var isLoading: Bool = false

    public init() {
        loadLinkedStudents()
    }

    public func loadLinkedStudents() {
        isLoading = true

        let child = StudentProfile(
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

        self.linkedStudents = [child]
        self.selectedStudent = child

        self.attendanceOverview = [
            AttendanceRecord(date: "31 Oct 2026", courseOrSubject: "Data Structures & Algorithms", status: "PRESENT"),
            AttendanceRecord(date: "30 Oct 2026", courseOrSubject: "Database Management Systems", status: "PRESENT"),
            AttendanceRecord(date: "29 Oct 2026", courseOrSubject: "Operating Systems", status: "PRESENT"),
            AttendanceRecord(date: "28 Oct 2026", courseOrSubject: "Computer Networks", status: "ABSENT", remarks: "Medical leave approved")
        ]

        self.recentResults = [
            AssessmentResult(term: "Mid-Term Exam", subjectName: "Data Structures", scoreObtained: 46.0, maxScore: 50.0, grade: "A+"),
            AssessmentResult(term: "Mid-Term Exam", subjectName: "Operating Systems", scoreObtained: 48.0, maxScore: 50.0, grade: "O")
        ]

        self.announcements = [
            AnnouncementItem(
                title: "Parent-Teacher Consultation Schedule",
                content: "Department faculty meetings will be held virtually on Saturday, 14 November 2026.",
                datePublished: "29 Oct 2026",
                authorRole: "Head of Academic Department",
                priority: "HIGH"
            )
        ]

        self.isLoading = false
    }
}

