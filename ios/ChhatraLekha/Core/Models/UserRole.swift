import Foundation

/// Persona driving the role-based navigation and security policies.
public enum UserRole: String, Codable, CaseIterable, Identifiable {
    case student = "student"
    case parent = "parent"
    case teacher = "faculty"
    case institution = "institution"
    case national = "national"
    case verifier = "verifier"

    public var id: String { rawValue }

    public var displayName: String {
        switch self {
        case .student:
            return "Student"
        case .parent:
            return "Parent / Guardian"
        case .teacher:
            return "Teacher / Faculty"
        case .institution:
            return "Institution Administrator"
        case .national:
            return "National Directorate"
        case .verifier:
            return "Third-Party Verifier"
        }
    }

    public var subtitle: String {
        switch self {
        case .student:
            return "Digital academic identity card, QR seal and academic wallet"
        case .parent:
            return "Attendance updates, examination results and school notices"
        case .teacher:
            return "Assigned classes, daily attendance marking and grading"
        case .institution:
            return "Intake quotas, batch CSV ingestion and student register"
        case .national:
            return "Pan-India compliance matrix, quota tracking and anomaly audit"
        case .verifier:
            return "Instant tamper-evident credential and degree verification"
        }
    }

    public var iconName: String {
        switch self {
        case .student:
            return "person.text.rectangle"
        case .parent:
            return "figure.2.and.child.holdinghands"
        case .teacher:
            return "rectangle.inset.filled.and.person.filled"
        case .institution:
            return "building.columns"
        case .national:
            return "chart.bar.doc.horizontal"
        case .verifier:
            return "qrcode.viewfinder"
        }
    }
}

