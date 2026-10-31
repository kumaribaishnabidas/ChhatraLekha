import Foundation

/// Voice intent catalogue for hands-free and multilingual navigation.
public enum VoiceIntent: String, CaseIterable {
    case dashboard
    case institutions
    case students
    case anomalies
    case reports
    case verify
    case attendance
    case results
    case studentCount
    case help
    case stop
    case darkTheme
    case lightTheme
}

/// Deterministic voice command parser supporting English, Hindi, and Odia.
public struct VoiceIntentMatcher {
    public static func match(text: String, language: String = "en") -> VoiceIntent? {
        let clean = text.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let lang = language.lowercased()

        if lang.starts(with: "or") {
            // Odia voice patterns
            if clean.contains("ଉପସ୍ଥାନ") || clean.contains("ହାଜିରା") {
                return .attendance
            }
            if clean.contains("ଫଳାଫଳ") || clean.contains("ନମ୍ବର") {
                return .results
            }
            if clean.contains("ଡ୍ୟାସବୋର୍ଡ") {
                return .dashboard
            }
            if clean.contains("ଛାତ୍ର") || clean.contains("ବିଦ୍ୟାର୍ଥୀ") {
                return .students
            }
            if clean.contains("ସାହାଯ୍ୟ") {
                return .help
            }
            if clean.contains("ରୁହ") || clean.contains("ବନ୍ଦ କର") {
                return .stop
            }
        }

        if lang.starts(with: "hi") {
            // Hindi voice patterns
            if clean.contains("उपस्थिति") || clean.contains("हाजिरी") {
                return .attendance
            }
            if clean.contains("परिणाम") || clean.contains("रिजल्ट") || clean.contains("अंक") {
                return .results
            }
            if clean.contains("डैशबोर्ड") {
                return .dashboard
            }
            if clean.contains("विद्यार्थी") || clean.contains("छात्र") {
                return .students
            }
            if clean.contains("मदद") || clean.contains("सहायता") {
                return .help
            }
            if clean.contains("रुको") || clean.contains("बंद करो") {
                return .stop
            }
        }

        // English voice patterns
        if clean.contains("attendance") || clean.contains("presence") {
            return .attendance
        }
        if clean.contains("results") || clean.contains("grades") || clean.contains("marks") {
            return .results
        }
        if clean.contains("dashboard") {
            return .dashboard
        }
        if clean.contains("students") || clean.contains("register") {
            return .students
        }
        if clean.contains("verify") {
            return .verify
        }
        if clean.contains("reports") {
            return .reports
        }
        if clean.contains("help") {
            return .help
        }
        if clean.contains("stop") || clean.contains("be quiet") {
            return .stop
        }

        return nil
    }
}

