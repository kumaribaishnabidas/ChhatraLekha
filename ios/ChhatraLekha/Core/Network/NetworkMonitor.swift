import Foundation
import Network
import Combine

/// Real-time cellular and Wi-Fi connectivity monitor using Network framework.
public final class NetworkMonitor: ObservableObject {
    public static let shared = NetworkMonitor()

    @Published public private(set) var isConnected: Bool = true
    @Published public private(set) var isCellular: Bool = false

    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "com.chhatralekha.app.networkmonitor")

    private init() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isConnected = path.status == .satisfied
                self?.isCellular = path.isExpensive
            }
        }
        monitor.start(queue: queue)
    }

    deinit {
        monitor.cancel()
    }
}

