import Foundation

public enum NetworkError: Error, LocalizedError {
    case invalidUrl
    case unauthorized
    case serverError(statusCode: Int, message: String?)
    case networkUnavailable
    case decodingError(Error)

    public var errorDescription: String? {
        switch self {
        case .invalidUrl:
            return "The requested endpoint URL is invalid."
        case .unauthorized:
            return "Session expired or invalid credentials. Please sign in again."
        case .serverError(let code, let msg):
            return msg ?? "Server returned error code \(code)."
        case .networkUnavailable:
            return "Network connection unavailable. Operating in offline mode."
        case .decodingError(let err):
            return "Data parsing error: \(err.localizedDescription)"
        }
    }
}

/// Robust asynchronous HTTP client integrated with secure storage and offline caches.
public final class ApiClient {
    public static let shared = ApiClient()
    public var baseUrl: String = "https://chhatralekha.onrender.com"

    private let session: URLSession

    public init(session: URLSession = .shared) {
        self.session = session
    }

    public func request<T: Decodable>(
        endpoint: ApiEndpoint,
        bodyData: Data? = nil,
        cacheKey: String? = nil
    ) async throws -> T {
        // Check offline availability first if network is disconnected
        if !NetworkMonitor.shared.isConnected, let key = cacheKey {
            if let cached: T = OfflineDataStore.shared.load(filename: key, type: T.self) {
                return cached
            }
            throw NetworkError.networkUnavailable
        }

        guard let url = URL(string: baseUrl + endpoint.path) else {
            throw NetworkError.invalidUrl
        }

        var request = URLRequest(url: url)
        request.httpMethod = endpoint.httpMethod
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if let token = KeychainManager.shared.retrieve(key: "auth_token") {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = bodyData {
            request.httpBody = body
        }

        do {
            let (data, response) = try await session.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                throw NetworkError.serverError(statusCode: 0, message: "Invalid HTTP response")
            }

            if httpResponse.statusCode == 401 {
                KeychainManager.shared.delete(key: "auth_token")
                throw NetworkError.unauthorized
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                let errorMessage = String(data: data, encoding: .utf8)
                throw NetworkError.serverError(statusCode: httpResponse.statusCode, message: errorMessage)
            }

            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            let decoded = try decoder.decode(T.self, from: data)

            // Cache successful response locally
            if let key = cacheKey, let encodable = decoded as? Encodable {
                OfflineDataStore.shared.save(encodable, filename: key)
            }

            return decoded
        } catch let netErr as NetworkError {
            throw netErr
        } catch {
            if let key = cacheKey, let cached: T = OfflineDataStore.shared.load(filename: key, type: T.self) {
                return cached
            }
            throw NetworkError.serverError(statusCode: 0, message: error.localizedDescription)
        }
    }

    public func executeRawMutation(
        endpoint: String,
        method: String,
        payloadJson: String
    ) async throws {
        guard let url = URL(string: baseUrl + endpoint) else {
            throw NetworkError.invalidUrl
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = KeychainManager.shared.retrieve(key: "auth_token") {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = payloadJson.data(using: .utf8)

        let (_, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.serverError(statusCode: (response as? HTTPURLResponse)?.statusCode ?? 500, message: "Mutation failed")
        }
    }
}

