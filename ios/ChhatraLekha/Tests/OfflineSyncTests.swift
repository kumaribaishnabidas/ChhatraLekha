import XCTest
@testable import ChhatraLekha

final class OfflineSyncTests: XCTestCase {
    func testQueuedMutationInitialization() {
        let mutation = QueuedMutation(
            endpoint: "/api/attendance/record",
            method: "POST",
            payloadJson: "{\"session\": \"Lab\"}"
        )
        XCTAssertEqual(mutation.status, .pending)
        XCTAssertEqual(mutation.retryCount, 0)
        XCTAssertEqual(mutation.method, "POST")
    }

    func testOfflineDataStoreSaveAndLoad() {
        let store = OfflineDataStore.shared
        let testProfile = StudentProfile(
            id: "std_test",
            apaarId: "984210357890",
            fullName: "Test Student",
            rollNumber: "ROLL-001",
            institutionId: "inst_101",
            institutionName: "Test Institution",
            program: "Test Program",
            gradeOrYear: "Year 1",
            section: "A",
            enrollmentYear: 2026
        )

        store.save(testProfile, filename: "test_profile_unit.json")
        let loaded = store.load(filename: "test_profile_unit.json", type: StudentProfile.self)
        XCTAssertNotNil(loaded)
        XCTAssertEqual(loaded?.fullName, "Test Student")
    }

    func testSyncStatusDisplayLabels() {
        XCTAssertEqual(SyncStatus.synced.displayLabel, "Synced")
        XCTAssertEqual(SyncStatus.pending.displayLabel, "Pending Sync")
        XCTAssertEqual(SyncStatus.inFlight.displayLabel, "Syncing...")
        XCTAssertEqual(SyncStatus.failed.displayLabel, "Sync Failed")
        XCTAssertEqual(SyncStatus.conflict.displayLabel, "Conflict Detected")
    }
}

