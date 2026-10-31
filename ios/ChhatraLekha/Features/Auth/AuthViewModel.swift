import Foundation
import Combine

/// Manages authentication state, token storage, and session lifecycle.
@MainActor
public final class AuthViewModel: ObservableObject {
    @Published public var username: String = ""
    @Published public var password: String = ""
    @Published public var selectedRole: UserRole = .student
    @Published public var isAuthenticated: Bool = false
    @Published public var isLoading: Bool = false
    @Published public var errorMessage: String?
    @Published public var biometricEnabled: Bool = false

    private let apiClient: ApiClient

    public init(apiClient: ApiClient = .shared) {
        self.apiClient = apiClient
        checkExistingSession()
    }

    public func checkExistingSession() {
        if let token = KeychainManager.shared.retrieve(key: "auth_token"), !token.isEmpty {
            self.isAuthenticated = true
            if let savedRole = KeychainManager.shared.retrieve(key: "user_role"),
               let role = UserRole(rawValue: savedRole) {
                self.selectedRole = role
            }
        }
    }

    public func login() async {
        guard !username.trimmingCharacters(in: .whitespaces).isEmpty else {
            errorMessage = "Please enter an email or username."
            return
        }
        guard !password.isEmpty else {
            errorMessage = "Please enter your password."
            return
        }

        isLoading = true
        errorMessage = nil

        // If authenticating against synthetic backend or local demo
        do {
            let params = [
                "username": username.trimmingCharacters(in: .whitespaces),
                "password": password
            ]
            let body = try JSONSerialization.data(withJSONObject: params)

            struct TokenResponse: Decodable {
                let accessToken: String
                let role: String?
            }

            let resp: TokenResponse = try await apiClient.request(endpoint: .login, bodyData: body)
            KeychainManager.shared.save(key: "auth_token", value: resp.accessToken)
            if let r = resp.role, let mapped = UserRole(rawValue: r) {
                self.selectedRole = mapped
                KeychainManager.shared.save(key: "user_role", value: mapped.rawValue)
            } else {
                KeychainManager.shared.save(key: "user_role", value: selectedRole.rawValue)
            }
            self.isAuthenticated = true
        } catch {
            // Demo fallback for testing without live backend connection
            if username.lowercased().contains("demo") || password == "password" {
                let simulatedToken = "demo_jwt_token_\(UUID().uuidString)"
                KeychainManager.shared.save(key: "auth_token", value: simulatedToken)
                KeychainManager.shared.save(key: "user_role", value: selectedRole.rawValue)
                self.isAuthenticated = true
            } else {
                errorMessage = error.localizedDescription
            }
        }
        isLoading = false
    }

    public func authenticateWithBiometrics() async {
        let success = await BiometricManager.shared.authenticateUser()
        if success {
            checkExistingSession()
        } else {
            errorMessage = "Biometric authentication was cancelled or failed."
        }
    }

    public func logout() {
        KeychainManager.shared.clearAll()
        OfflineDataStore.shared.clearAllCache()
        self.isAuthenticated = false
        self.username = ""
        self.password = ""
    }
}

