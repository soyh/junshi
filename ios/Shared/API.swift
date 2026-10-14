import Foundation

enum ClientError: LocalizedError {
    case message(String), unauthorized
    var errorDescription: String? {
        switch self { case .message(let text): return text; case .unauthorized: return "登录已失效，请重新登录。" }
    }
}
enum ServerPolicy {
    static func origin(_ input: String) throws -> URL {
        guard var c = URLComponents(string: input.trimmingCharacters(in: .whitespacesAndNewlines)),
              c.scheme?.lowercased() == "https", let host = c.host, !host.isEmpty,
              c.user == nil, c.password == nil, c.query == nil, c.fragment == nil,
              ["", "/", "/app", "/app/"].contains(c.path),
              c.port == nil || (1...65535).contains(c.port!) else {
            throw ClientError.message("请填写 HTTPS 服务器地址，不含账号密码、查询参数或其他路径。")
        }
        c.scheme = "https"; c.host = host.lowercased(); c.path = ""
        guard let url = c.url else { throw ClientError.message("服务器地址无效。") }
        return url
    }
    static func sameOrigin(_ a: URL, _ b: URL) -> Bool {
        a.scheme?.lowercased() == b.scheme?.lowercased() && a.host?.lowercased() == b.host?.lowercased() && (a.port ?? 443) == (b.port ?? 443)
    }
}
final class NoRedirect: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) { completionHandler(nil) }
}
protocol APITransport {
    func request(_ method: String, _ path: String, body: [String: Any]?) async throws -> Data
    func upload(_ path: String, item: MediaItem, operation: String, sentAt: String) async throws -> Data
}
extension APITransport {
    func decode<T: Decodable>(_ method: String, _ path: String, body: [String: Any]? = nil, as type: T.Type = T.self) async throws -> T {
        let data = try await request(method, path, body: body)
        return try JSONDecoder().decode(type, from: data)
    }
}
final class API: APITransport, @unchecked Sendable {
    let origin: URL
    let token: String?
    private let session: URLSession
    init(server: String, token: String? = nil, configuration: URLSessionConfiguration = .ephemeral) throws {
        origin = try ServerPolicy.origin(server); self.token = token
        configuration.timeoutIntervalForRequest = 300; configuration.timeoutIntervalForResource = 360
        configuration.urlCache = nil; configuration.httpCookieStorage = nil
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("-ui-testing") { configuration.protocolClasses = [FixtureProtocol.self] }
        #endif
        session = URLSession(configuration: configuration, delegate: NoRedirect(), delegateQueue: nil)
    }
    deinit { session.invalidateAndCancel() }
    private func makeRequest(_ method: String, _ path: String) throws -> URLRequest {
        guard path.hasPrefix("/"), !path.contains(".."), !path.contains("#"),
              let url = URL(string: origin.absoluteString + "/api/v1" + path), ServerPolicy.sameOrigin(origin, url) else { throw ClientError.message("接口地址无效。") }
        var request = URLRequest(url: url); request.httpMethod = method
        if let token { request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization") }
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        return request
    }
    private func checked(_ data: Data, _ response: URLResponse) throws -> Data {
        guard data.count <= 4 * 1024 * 1024, let response = response as? HTTPURLResponse else { throw ClientError.message("服务器响应过大或无效。") }
        if response.statusCode == 401 { throw ClientError.unauthorized }
        if (300..<400).contains(response.statusCode) { throw ClientError.message("服务器发生重定向，请核对 HTTPS 地址。") }
        guard (200..<300).contains(response.statusCode) else {
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
            throw ClientError.message(detail ?? "服务器返回 HTTP \(response.statusCode)，请检查输入与服务器配置。")
        }
        return data
    }
    func request(_ method: String, _ path: String, body: [String: Any]? = nil) async throws -> Data {
        var request = try makeRequest(method, path)
        if let body { request.httpBody = try JSONSerialization.data(withJSONObject: body); request.setValue("application/json", forHTTPHeaderField: "Content-Type") }
        do { let (data, response) = try await session.data(for: request); return try checked(data, response) }
        catch let e as URLError where e.code == .timedOut { throw ClientError.message("请求超时。保持本次输入重试，已保存的记录不会重复导入。") }
    }
    func upload(_ path: String, item: MediaItem, operation: String, sentAt: String) async throws -> Data {
        let boundary = "Junshi-" + UUID().uuidString
        let spool = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".multipart")
        FileManager.default.createFile(atPath: spool.path, contents: nil, attributes: [.protectionKey: FileProtectionType.complete])
        defer { try? FileManager.default.removeItem(at: spool) }
        let out = try FileHandle(forWritingTo: spool)
        do {
            func write(_ value: String) throws { try out.write(contentsOf: Data(value.utf8)) }
            for (name, value) in [("operation_id", operation), ("sent_at", sentAt)] {
                try write("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(name)\"\r\n\r\n\(value)\r\n")
            }
            try write("--\(boundary)\r\nContent-Disposition: form-data; name=\"file\"; filename=\"attachment.\(item.ext)\"\r\nContent-Type: \(item.mime)\r\n\r\n")
            try MediaIO.copyBytes(item.url, into: out)
            try write("\r\n--\(boundary)--\r\n"); try out.close()
        } catch { try? out.close(); throw error }
        var request = try makeRequest("POST", path)
        request.setValue("multipart/form-data; boundary=" + boundary, forHTTPHeaderField: "Content-Type")
        let (data, response) = try await session.upload(for: request, fromFile: spool)
        return try checked(data, response)
    }
}
struct Person: Codable, Identifiable { let id: String; let name: String; var nickname: String? }
struct Conversation: Codable, Identifiable { let id: String; let title: String? }
struct PlatformAccount: Codable, Identifiable {
    let id: String; let platform: String; let account_handle: String; let display_name: String?
    var label: String { platform + " · " + (display_name?.isEmpty == false ? display_name! : account_handle) }
}
struct ModelProfile: Codable, Identifiable { let id: String; let name: String; let provider: String; let model: String; let is_active: Bool }
struct LoginResult: Decodable { let access_token: String }
struct ChallengeResult: Decodable { let challenge_id: String; let message: String }
struct ReplyResult: Decodable { let draft: String? }
struct IDResult: Decodable { let id: String }
struct TicketResult: Decodable { let ticket: String }
enum Registration {
    static func validate(_ username: String, _ password: String) throws {
        guard username.range(of: "^[A-Za-z0-9._-]{3,64}$", options: .regularExpression) != nil else { throw ClientError.message("账号需为 3–64 位英文字母、数字、点、下划线或短横线。") }
        guard (12...256).contains(password.unicodeScalars.count) else { throw ClientError.message("密码需为 12–256 个字符，不强制特殊符号。") }
    }
}
enum ChinaTime {
    static func timestamp(_ date: Date) -> String {
        let f = ISO8601DateFormatter(); f.timeZone = TimeZone(secondsFromGMT: 28800)
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]; return f.string(from: date)
    }
}
