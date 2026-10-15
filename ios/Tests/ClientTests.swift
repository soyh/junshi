import XCTest
@testable import Junshi

final class ClientTests: XCTestCase {
    func testTransportPreservesDefiniteRejectionForCorrectableInput() async throws {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [RejectedCreationProtocol.self]
        let api = try API(server:"https://synthetic.example",configuration:config)
        do { _ = try await api.request("POST","/persons",body:["name":""]); XCTFail("Expected input rejection") }
        catch let error as ClientError {
            guard case .http(let status, let message) = error else { return XCTFail("Lost HTTP classification") }
            XCTAssertEqual(status,422); XCTAssertEqual(message,"name required")
            XCTAssertTrue(error.creationDefinitelyRejected)
        }
    }
    func testCreationRecoveryDistinguishesRejectionFromUncertainCommit() {
        for code in [400, 403, 404, 409, 422] { XCTAssertTrue(ClientError.http(code,"input rejected").creationDefinitelyRejected) }
        for code in [408, 429, 500, 502, 503, 504] { XCTAssertFalse(ClientError.http(code,"unknown outcome").creationDefinitelyRejected) }
        XCTAssertFalse(ClientError.message("timeout after server commit").creationDefinitelyRejected)
        XCTAssertFalse(ClientError.unauthorized.creationDefinitelyRejected)
    }

    func testHTTPSOriginRejectsCredentialAndPathConfusion() throws {
        XCTAssertEqual(try ServerPolicy.origin("https://example.com/app/").absoluteString,"https://example.com")
        for input in ["http://example.com","https://user:password@example.com","https://example.com/path","https://example.com?token=x","https://example.com#token=x"] { XCTAssertThrowsError(try ServerPolicy.origin(input)) }
        XCTAssertFalse(ServerPolicy.sameOrigin(URL(string:"https://example.com")!,URL(string:"https://example.com.evil.test")!))
        XCTAssertFalse(ServerPolicy.sameOrigin(URL(string:"https://example.com:443")!,URL(string:"https://example.com:444")!))
    }
    func testRegistrationAndChinaTime() throws {
        try Registration.validate("test-user",String(repeating:"a",count:12))
        XCTAssertThrowsError(try Registration.validate("中文账号",String(repeating:"a",count:12)))
        XCTAssertThrowsError(try Registration.validate("valid_user","short"))
        XCTAssertTrue(ChinaTime.timestamp(Date(timeIntervalSince1970:0)).hasPrefix("1970-01-01T08:00:00"))
        XCTAssertTrue(ChinaTime.timestamp(Date()).hasSuffix("+08:00"))
    }
    func testShareIsScopedAndFilesCannotTraverse() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at:root) }
        let name = "JunshiTests."+UUID().uuidString, defaults = UserDefaults(suiteName:name)!
        defer { defaults.removePersistentDomain(forName:name) }
        let inbox = try ShareInbox(root:root,defaults:defaults)
        try inbox.bind("owner-a"); try inbox.save(text:"synthetic text",media:[],owner:"owner-a")
        XCTAssertEqual(try inbox.read(for:"owner-a")?.text,"synthetic text")
        XCTAssertThrowsError(try inbox.save(text:"second",media:[],owner:"owner-a"))
        XCTAssertThrowsError(try inbox.file(SharedFile(name:"../outside.mp4",mime:"video/mp4",ext:"mp4")))
        try inbox.bind("owner-b"); XCTAssertNil(try inbox.read(for:"owner-b"))
        XCTAssertThrowsError(try inbox.save(text:"old-owner",media:[],owner:"owner-a"))
        try Data("invalid JSON".utf8).write(to:root.appendingPathComponent("pending.json"))
        try inbox.bind(nil); XCTAssertFalse(FileManager.default.fileExists(atPath:root.appendingPathComponent("pending.json").path))
    }
    func testMediaCopiesAndRejectsEmptyFile() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        defer { try? FileManager.default.removeItem(at:root) }
        let source = root.appendingPathComponent("source.mp4")
        try Data("synthetic media bytes".utf8).write(to:source)
        let item = try MediaIO.importFile(source,directory:root)
        XCTAssertEqual(try Data(contentsOf:item.url),try Data(contentsOf:source))
        let empty = root.appendingPathComponent("empty.mp4"); try Data().write(to:empty)
        XCTAssertThrowsError(try MediaIO.importFile(empty,directory:root))
    }
    @MainActor func testRetryUsesSameOperationAndConfirmationCannotChange() async throws {
        let api = FakeTransport(); api.failMessageOnce = true
        let job = GenerateJob(person:"p1",conversation:"c1",text:"hello",sentAt:Date(),media:[])
        do { _ = try await job.generate(api); XCTFail("Expected simulated timeout") } catch {}
        let reply = try await job.generate(api); XCTAssertEqual(reply,"synthetic reply")
        XCTAssertEqual(Set(api.messageOperations).count,1)
        api.failMessageOnce = true
        do { try await job.confirm(api,reply:"sent text"); XCTFail("Expected uncertain confirmation") } catch {}
        do { try await job.confirm(api,reply:"different text"); XCTFail("Cannot change uncertain reply") } catch {}
        try await job.confirm(api,reply:"sent text")
        let count = api.messageOperations.count
        try await job.confirm(api,reply:"sent text"); XCTAssertEqual(api.messageOperations.count,count)
    }
    @MainActor func testFailedAnalysisDoesNotReuploadMedia() async throws {
        let api = FakeTransport(); api.failAnalysisOnce = true
        let item = MediaItem(url:URL(fileURLWithPath:"/synthetic.mp4"),mime:"video/mp4",ext:"mp4")
        let job = GenerateJob(person:"p1",conversation:"c1",text:"",sentAt:Date(),media:[item])
        do { _ = try await job.generate(api); XCTFail("Expected analysis error") } catch {}
        _ = try await job.generate(api); XCTAssertEqual(api.uploadCount,1)
    }
}
@MainActor final class FakeTransport: APITransport {
    var failMessageOnce = false, failAnalysisOnce = false, messageOperations: [String] = [], uploadCount = 0
    func request(_ method: String, _ path: String, body: [String:Any]?) async throws -> Data {
        if path == "/pc/messages" {
            messageOperations.append(body!["operation_id"] as! String)
            if failMessageOnce { failMessageOnce = false; throw ClientError.message("simulated timeout after server commit") }
        }
        if path.contains("/analyze"), failAnalysisOnce { failAnalysisOnce = false; throw ClientError.message("simulated analysis failure") }
        return path.contains("strategic-reply") ? Data("{\"draft\":\"synthetic reply\"}".utf8) : Data("{}".utf8)
    }
    func upload(_ path: String, item: MediaItem, operation: String, sentAt: String) async throws -> Data { uploadCount += 1; return Data("{\"id\":\"media-1\"}".utf8) }
}

final class RejectedCreationProtocol: URLProtocol {
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        let response=HTTPURLResponse(url:request.url!,statusCode:422,httpVersion:nil,headerFields:["Content-Type":"application/json"])!
        client?.urlProtocol(self,didReceive:response,cacheStoragePolicy:.notAllowed)
        client?.urlProtocol(self,didLoad:Data("{\"detail\":\"name required\"}".utf8))
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}
