import Foundation

/// Local offline persistence store ensuring complete offline-first access.
public final class OfflineDataStore {
    public static let shared = OfflineDataStore()
    private let queue = DispatchQueue(label: "com.chhatralekha.app.datastore", attributes: .concurrent)
    private let fileManager = FileManager.default

    private init() {
        createStorageDirectoriesIfNeeded()
    }

    private var storageDirectory: URL {
        let urls = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask)
        let dir = urls[0].appendingPathComponent("ChhatraLekhaStorage", isDirectory: true)
        return dir
    }

    private func createStorageDirectoriesIfNeeded() {
        if !fileManager.fileExists(atPath: storageDirectory.path) {
            try? fileManager.createDirectory(at: storageDirectory, withIntermediateDirectories: true)
        }
    }

    public func save<T: Encodable>(_ item: T, filename: String) {
        queue.async(flags: .barrier) { [weak self] in
            guard let self = self else { return }
            let fileURL = self.storageDirectory.appendingPathComponent(filename)
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            if let data = try? encoder.encode(item) {
                try? data.write(to: fileURL, options: .atomic)
            }
        }
    }

    public func load<T: Decodable>(filename: String, type: T.Type) -> T? {
        queue.sync {
            let fileURL = storageDirectory.appendingPathComponent(filename)
            guard let data = try? Data(contentsOf: fileURL) else { return nil }
            let decoder = JSONDecoder()
            return try? decoder.decode(type, from: data)
        }
    }

    public func clearAllCache() {
        queue.async(flags: .barrier) { [weak self] in
            guard let self = self else { return }
            try? self.fileManager.removeItem(at: self.storageDirectory)
            self.createStorageDirectoriesIfNeeded()
        }
    }
}

