import XCTest
@testable import ChhatraLekha

final class VoiceIntentMatcherTests: XCTestCase {
    func testEnglishVoiceCommands() {
        XCTAssertEqual(VoiceIntentMatcher.match(text: "show my attendance"), .attendance)
        XCTAssertEqual(VoiceIntentMatcher.match(text: "open dashboard"), .dashboard)
        XCTAssertEqual(VoiceIntentMatcher.match(text: "check my results"), .results)
        XCTAssertEqual(VoiceIntentMatcher.match(text: "stop"), .stop)
    }

    func testHindiVoiceCommands() {
        XCTAssertEqual(VoiceIntentMatcher.match(text: "डैशबोर्ड खोलें", language: "hi-IN"), .dashboard)
        XCTAssertEqual(VoiceIntentMatcher.match(text: "मेरी उपस्थिति दिखाओ", language: "hi-IN"), .attendance)
        XCTAssertEqual(VoiceIntentMatcher.match(text: "रुको", language: "hi-IN"), .stop)
    }

    func testOdiaVoiceCommands() {
        XCTAssertEqual(VoiceIntentMatcher.match(text: "ମୋର ଆଜିର ଉପସ୍ଥାନ ଦେଖାଅ", language: "or-IN"), .attendance)
        XCTAssertEqual(VoiceIntentMatcher.match(text: "ମୋର ପରୀକ୍ଷା ଫଳାଫଳ ଦେଖାଅ", language: "or-IN"), .results)
        XCTAssertEqual(VoiceIntentMatcher.match(text: "ଡ୍ୟାସବୋର୍ଡ", language: "or-IN"), .dashboard)
    }

    func testUnknownCommandReturnsNil() {
        XCTAssertNil(VoiceIntentMatcher.match(text: "make an unauthorized modification now"))
    }
}

