import Foundation

/// Deterministic 12-digit APAAR format and checksum validation engine.
public struct ApaarValidator {
    public enum ValidationError: Error, LocalizedError {
        case empty
        case invalidLength
        case nonNumeric
        case allIdenticalDigits
        case checksumMismatch

        public var errorDescription: String? {
            switch self {
            case .empty:
                return "APAAR ID cannot be empty."
            case .invalidLength:
                return "APAAR ID must contain exactly 12 numeric digits."
            case .nonNumeric:
                return "APAAR ID must only contain decimal digits."
            case .allIdenticalDigits:
                return "APAAR ID cannot consist of repetitive single digits."
            case .checksumMismatch:
                return "APAAR ID failed deterministic checksum verification."
            }
        }
    }

    public static func validate(_ raw: String) -> Result<String, ValidationError> {
        let cleaned = raw.replacingOccurrences(of: " ", with: "")
            .replacingOccurrences(of: "-", with: "")

        guard !cleaned.isEmpty else { return .failure(.empty) }
        guard cleaned.count == 12 else { return .failure(.invalidLength) }
        guard CharacterSet.decimalDigits.isSuperset(of: CharacterSet(charactersIn: cleaned)) else {
            return .failure(.nonNumeric)
        }

        // Prohibit all repeated digits like 000000000000 or 111111111111
        let firstChar = cleaned.first!
        if cleaned.allSatisfy({ $0 == firstChar }) {
            return .failure(.allIdenticalDigits)
        }

        // Luhn checksum test
        var sum = 0
        let digits = cleaned.compactMap { $0.wholeNumberValue }
        for (index, digit) in digits.reversed().enumerated() {
            if index % 2 == 1 {
                let doubled = digit * 2
                sum += doubled > 9 ? (doubled - 9) : doubled
            } else {
                sum += digit
            }
        }

        guard sum % 10 == 0 else {
            return .failure(.checksumMismatch)
        }

        return .success(cleaned)
    }
}

