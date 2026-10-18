import XCTest

final class FlowTests: XCTestCase {
    func testLoginPersonSelectionAndReplyFlow() {
        let app = XCUIApplication(); app.launchArguments = ["-ui-testing"]; app.launch()
        let server = app.textFields["server"]; XCTAssertTrue(server.waitForExistence(timeout:10))
        server.tap(); server.typeText("https://synthetic.example")
        app.textFields["username"].tap(); app.textFields["username"].typeText("synthetic-user")
        app.secureTextFields["password"].tap(); app.secureTextFields["password"].typeText("synthetic-password")
        app.buttons["login-submit"].tap()
        XCTAssertTrue(app.buttons["person-p1"].waitForExistence(timeout:10), "Login did not finish: " + app.staticTexts["status"].label + "\n" + app.debugDescription)
        app.buttons["person-p1"].tap()
        let picker = app.buttons["conversation-picker"]; XCTAssertTrue(picker.waitForExistence(timeout:5)); picker.tap()
        app.buttons["测试会话"].tap()
        let incoming = app.textViews["incoming-text"]; incoming.tap(); incoming.typeText("你在干嘛呢？")
        if app.buttons["完成"].exists { app.buttons["完成"].tap() }
        app.buttons["generate"].tap()
        let reply = app.textViews["reply-draft"]
        let predicate = NSPredicate(format:"value CONTAINS %@","刚忙完")
        expectation(for:predicate,evaluatedWith:reply); waitForExpectations(timeout:10)
        app.swipeUp(); app.buttons["confirm-sent"].tap()
        let status = app.staticTexts["status"]
        expectation(for:NSPredicate(format:"label CONTAINS %@","已登记"),evaluatedWith:status); waitForExpectations(timeout:10)
        let screenshot = XCTAttachment(screenshot:app.screenshot()); screenshot.name = "iOS-blue-white-workspace"; screenshot.lifetime = .keepAlways; add(screenshot)
    }
    func testCreatesAdditionalConversationForCurrentPerson() {
        let app = XCUIApplication(); app.launchArguments = ["-ui-testing"]; app.launch()
        let server = app.textFields["server"]; XCTAssertTrue(server.waitForExistence(timeout:10))
        server.tap(); server.typeText("https://synthetic.example")
        app.textFields["username"].tap(); app.textFields["username"].typeText("synthetic-user")
        app.secureTextFields["password"].tap(); app.secureTextFields["password"].typeText("synthetic-password")
        app.buttons["login-submit"].tap()
        XCTAssertTrue(app.buttons["person-p1"].waitForExistence(timeout:10))
        app.buttons["person-p1"].tap()
        let newConversation = app.buttons["new-conversation"]
        XCTAssertTrue(newConversation.waitForExistence(timeout:10))
        newConversation.tap()
        let title = app.textFields["conversation-title"]; XCTAssertTrue(title.waitForExistence(timeout:5))
        title.tap(); title.typeText("Second conversation")
        app.buttons["create-conversation"].tap()
        let status = app.staticTexts["status"]
        expectation(for:NSPredicate(format:"label CONTAINS %@","会话已创建并打开"),evaluatedWith:status)
        waitForExpectations(timeout:10)
    }

}
