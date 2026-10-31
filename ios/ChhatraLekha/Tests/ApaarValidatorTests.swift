import XCTest
@testable import ChhatraLekha

final class ApaarValidatorTests: XCTestCase {
    func testEmptyApaarIdFails() {
        let result = ApaarValidator.validate("")
        switch result {
        case .failure(let error):
            XCTAssertEqual(error, .empty)
        case .success:
            XCTFail("Empty APAAR should fail")
        }
    }

    func testIncorrectLengthFails() {
        let shortResult = ApaarValidator.validate("98421035")
        switch shortResult {
        case .failure(let error):
            XCTAssertEqual(error, .invalidLength)
        case .success:
            XCTFail("Short APAAR should fail")
        }

        let longResult = ApaarValidator.validate("984210357890123")
        switch longResult {
        case .failure(let error):
            XCTAssertEqual(error, .invalidLength)
        case .success:
            XCTFail("Long APAAR should fail")
        }
    }

    func testNonNumericCharactersFail() {
        let alphaResult = ApaarValidator.validate("98421035ABCD")
        switch alphaResult {
        case .failure(let error):
            XCTAssertEqual(error, .nonNumeric)
        case .success:
            XCTFail("Alpha characters should fail")
        }
    }

    func testRepeatedDigitsFail() {
        let zeroResult = ApaarValidator.validate("000000000000")
        switch zeroResult {
        case .failure(let error):
            XCTAssertEqual(error, .allIdenticalDigits)
        case .success:
            XCTFail("Repeated zeros should fail")
        }

        let oneResult = ApaarValidator.validate("111111111111")
        switch oneResult {
        case .failure(let error):
            XCTAssertEqual(error, .allIdenticalDigits)
        case .success:
            XCTFail("Repeated ones should fail")
        }
    }
}

