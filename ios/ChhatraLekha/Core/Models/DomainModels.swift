import Foundation

/// Core student academic record representation matching backend schemas.
public struct StudentProfile: Codable, Identifiable, Equatable {
    public let id: String
    public let apaarId: String
    public let fullName: String
    public let rollNumber: String
    public let institutionId: String
    public let institutionName: String
    public let program: String
    public let gradeOrYear: String
    public let section: String
    public let enrollmentYear: Int
    public let status: String
    public let guardianName: String?
    public let guardianContact: String?
    public let attendancePercentage: Double
    public let cgpaOrPercentage: Double

    public init(
        id: String,
        apaarId: String,
        fullName: String,
        rollNumber: String,
        institutionId: String,
        institutionName: String,
        program: String,
        gradeOrYear: String,
        section: String,
        enrollmentYear: Int,
        status: String = "ACTIVE",
        guardianName: String? = nil,
        guardianContact: String? = nil,
        attendancePercentage: Double = 92.5,
        cgpaOrPercentage: Double = 8.8
    ) {
        self.id = id
        self.apaarId = apaarId
        self.fullName = fullName
        self.rollNumber = rollNumber
        self.institutionId = institutionId
        self.institutionName = institutionName
        self.program = program
        self.gradeOrYear = gradeOrYear
        self.section = section
        self.enrollmentYear = enrollmentYear
        self.status = status
        self.guardianName = guardianName
        self.guardianContact = guardianContact
        self.attendancePercentage = attendancePercentage
        self.cgpaOrPercentage = cgpaOrPercentage
    }

    /// Redacted APAAR for non-privileged displays: e.g. 9842 **** 1234
    public var maskedApaarId: String {
        guard apaarId.count == 12 else { return apaarId }
        let prefix = apaarId.prefix(4)
        let suffix = apaarId.suffix(4)
        return "\(prefix) **** \(suffix)"
    }
}

/// Verifiable credential token issued to the student.
public struct AcademicCredential: Codable, Identifiable, Equatable {
    public let id: String
    public let title: String
    public let credentialType: String
    public let issuingInstitution: String
    public let issueDate: String
    public let verificationToken: String
    public let sealHash: String
    public let isRevoked: Bool

    public init(
        id: String,
        title: String,
        credentialType: String,
        issuingInstitution: String,
        issueDate: String,
        verificationToken: String,
        sealHash: String,
        isRevoked: Bool = false
    ) {
        self.id = id
        self.title = title
        self.credentialType = credentialType
        self.issuingInstitution = issuingInstitution
        self.issueDate = issueDate
        self.verificationToken = verificationToken
        self.sealHash = sealHash
        self.isRevoked = isRevoked
    }
}

/// Daily or session-based attendance entry.
public struct AttendanceRecord: Codable, Identifiable, Equatable {
    public let id: String
    public let date: String
    public let courseOrSubject: String
    public let status: String
    public let remarks: String?

    public init(
        id: String = UUID().uuidString,
        date: String,
        courseOrSubject: String,
        status: String,
        remarks: String? = nil
    ) {
        self.id = id
        self.date = date
        self.courseOrSubject = courseOrSubject
        self.status = status
        self.remarks = remarks
    }
}

/// Assessment exam score or term mark.
public struct AssessmentResult: Codable, Identifiable, Equatable {
    public let id: String
    public let term: String
    public let subjectName: String
    public let scoreObtained: Double
    public let maxScore: Double
    public let grade: String

    public init(
        id: String = UUID().uuidString,
        term: String,
        subjectName: String,
        scoreObtained: Double,
        maxScore: Double,
        grade: String
    ) {
        self.id = id
        self.term = term
        self.subjectName = subjectName
        self.scoreObtained = scoreObtained
        self.maxScore = maxScore
        self.grade = grade
    }
}

/// Official campus announcement or alert.
public struct AnnouncementItem: Codable, Identifiable, Equatable {
    public let id: String
    public let title: String
    public let content: String
    public let datePublished: String
    public let authorRole: String
    public let priority: String

    public init(
        id: String = UUID().uuidString,
        title: String,
        content: String,
        datePublished: String,
        authorRole: String,
        priority: String = "NORMAL"
    ) {
        self.id = id
        self.title = title
        self.content = content
        self.datePublished = datePublished
        self.authorRole = authorRole
        self.priority = priority
    }
}

/// Public verification verdict returned when inspecting a token badge.
public struct VerificationVerdict: Codable, Equatable {
    public let isValid: Bool
    public let token: String
    public let institutionName: String
    public let program: String
    public let session: String
    public let issueDate: String
    public let sealType: String
    public let message: String

    public init(
        isValid: Bool,
        token: String,
        institutionName: String,
        program: String,
        session: String,
        issueDate: String,
        sealType: String,
        message: String
    ) {
        self.isValid = isValid
        self.token = token
        self.institutionName = institutionName
        self.program = program
        self.session = session
        self.issueDate = issueDate
        self.sealType = sealType
        self.message = message
    }
}

