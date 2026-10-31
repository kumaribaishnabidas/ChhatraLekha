import XCTest
@testable import ChhatraLekha

final class DomainModelsTests: XCTestCase {
    func testStudentProfileMaskedApaarId() {
        let profile = StudentProfile(
            id: "std_001",
            apaarId: "984210357890",
            fullName: "Aarav Sharma",
            rollNumber: "2024-CS-042",
            institutionId: "inst_101",
            institutionName: "Delhi Public College",
            program: "Computer Science",
            gradeOrYear: "Sem IV",
            section: "A",
            enrollmentYear: 2024
        )
        XCTAssertEqual(profile.maskedApaarId, "9842 **** 7890")
    }

    func testSerializationRoundTrip() throws {
        let original = AcademicCredential(
            id: "cred_01",
            title: "Semester Grade Sheet",
            credentialType: "TRANSCRIPT",
            issuingInstitution: "Delhi Public College",
            issueDate: "15 Jan 2026",
            verificationToken: "tok_test_123",
            sealHash: "abcdef123456"
        )
        let encoder = JSONEncoder()
        let data = try encoder.encode(original)
        let decoder = JSONDecoder()
        let decoded = try decoder.decode(AcademicCredential.self, from: data)
        XCTAssertEqual(original, decoded)
    }

    func testUserRoleDisplayNames() {
        XCTAssertEqual(UserRole.student.displayName, "Student")
        XCTAssertEqual(UserRole.parent.displayName, "Parent / Guardian")
        XCTAssertEqual(UserRole.teacher.displayName, "Teacher / Faculty")
        XCTAssertEqual(UserRole.institution.displayName, "Institution Administrator")
        XCTAssertEqual(UserRole.verifier.displayName, "Third-Party Verifier")
    }
}

