import Foundation

/// API Endpoints supported by the unified ChhatraLekha backend.
public enum ApiEndpoint {
    case login
    case forgotPassword
    case studentProfile(apaarId: String)
    case studentCredentials(apaarId: String)
    case attendance(institutionId: String, grade: String)
    case recordAttendance
    case assessmentResults(studentId: String)
    case announcements(institutionId: String)
    case verifyToken(token: String)
    case auditEvents(institutionId: String)

    public var path: String {
        switch self {
        case .login:
            return "/api/auth/token"
        case .forgotPassword:
            return "/api/auth/forgot-password"
        case .studentProfile(let apaarId):
            return "/api/students/\(apaarId)"
        case .studentCredentials(let apaarId):
            return "/api/students/\(apaarId)/tokens"
        case .attendance(let instId, let grade):
            return "/api/institutions/\(instId)/attendance?grade=\(grade)"
        case .recordAttendance:
            return "/api/attendance/record"
        case .assessmentResults(let studentId):
            return "/api/students/\(studentId)/results"
        case .announcements(let instId):
            return "/api/institutions/\(instId)/announcements"
        case .verifyToken(let token):
            return "/api/tokens/verify/\(token)"
        case .auditEvents(let instId):
            return "/api/institutions/\(instId)/audit"
        }
    }

    public var httpMethod: String {
        switch self {
        case .login, .forgotPassword, .recordAttendance:
            return "POST"
        default:
            return "GET"
        }
    }
}

