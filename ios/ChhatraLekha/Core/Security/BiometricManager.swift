import Foundation
import LocalAuthentication

/// Biometric authentication helper for Face ID and Touch ID.
public final class BiometricManager {
    public static let shared = BiometricManager()

    private init() {}

    public enum BiometricType {
        case none
        case touchID
        case faceID
    }

    public var biometricType: BiometricType {
        let context = LAContext()
        var error: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            return .none
        }
        if #available(iOS 11.0, *) {
            switch context.biometryType {
            case .faceID:
                return .faceID
            case .touchID:
                return .touchID
            case .none:
                return .none
            @unknown default:
                return .none
            }
        }
        return .touchID
    }

    public func authenticateUser(reason: String = "Unlock ChhatraLekha academic identity") async -> Bool {
        let context = LAContext()
        context.localizedCancelTitle = "Cancel"
        var error: NSError?

        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            return false
        }

        do {
            return try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics,
                localizedReason: reason
            )
        } catch {
            return false
        }
    }
}

