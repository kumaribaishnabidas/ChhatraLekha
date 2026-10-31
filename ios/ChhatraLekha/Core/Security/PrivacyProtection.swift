import Foundation

/// Privacy safeguards adhering to the Digital Personal Data Protection (DPDP) Act 2023.
public struct PrivacyProtection {
    /// Mask a 12-digit APAAR identifier: e.g. "9842 1234 5678" -> "9842 **** 5678"
    public static func maskApaarId(_ raw: String) -> String {
        let clean = raw.replacingOccurrences(of: " ", with: "")
        guard clean.count == 12 else { return raw }
        let start = clean.prefix(4)
        let end = clean.suffix(4)
        return "\(start) **** \(end)"
    }

    /// Verifies if a student is legally a minor (under 18 years old) requiring guardian consent.
    public static func isMinor(birthDate: Date) -> Bool {
        let calendar = Calendar.current
        let ageComponents = calendar.dateComponents([.year], from: birthDate, to: Date())
        let age = ageComponents.year ?? 0
        return age < 18
    }

    /// Strips any confidential fields from sharing payloads, ensuring only opaque verification tokens are transmitted.
    public static func sanitizeForPublicShare(token: String) -> URL? {
        var components = URLComponents()
        components.scheme = "https"
        components.host = "chhatralekha.vercel.app"
        components.path = "/verify/t/\(token)"
        return components.url
    }
}

