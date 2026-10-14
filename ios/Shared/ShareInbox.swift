import Foundation
import CryptoKit

struct SharedFile: Codable { let name: String; let mime: String; let ext: String }
struct PendingShare: Codable, Identifiable { let id: UUID; let owner: String; let text: String; let files: [SharedFile]; let created: Date }
final class ShareInbox {
    let root: URL
    private let defaults: UserDefaults
    var owner: String? { defaults.string(forKey:"share-owner") }
    static func fingerprint(server: String, token: String) -> String { SHA256.hash(data:Data((server + "\n" + token).utf8)).map { String(format:"%02x",$0) }.joined() }
    static func configured() throws -> ShareInbox {
        guard let name = Bundle.main.object(forInfoDictionaryKey:"JunshiAppGroup") as? String,
              let root = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier:name),
              let defaults = UserDefaults(suiteName:name) else { throw ClientError.message("分享入口尚未配置 App Groups 签名；App 基础功能仍可使用。") }
        return try ShareInbox(root:root.appendingPathComponent("Inbox"), defaults:defaults)
    }
    init(root: URL, defaults: UserDefaults) throws {
        self.root = root; self.defaults = defaults
        try FileManager.default.createDirectory(at:root, withIntermediateDirectories:true, attributes:[.protectionKey:FileProtectionType.complete])
    }
    func bind(_ fingerprint: String?) throws {
        if owner != fingerprint { try clear() }
        if let fingerprint { defaults.set(fingerprint,forKey:"share-owner") } else { defaults.removeObject(forKey:"share-owner") }
    }
    private var packet: URL { root.appendingPathComponent("pending.json") }
    func save(text: String, media: [MediaItem], owner expected: String) throws {
        guard owner == expected else { throw ClientError.message("登录账号已变化，请回 App 核对后重新分享。") }
        guard text.unicodeScalars.count <= 100000, media.count <= 4, !text.isEmpty || !media.isEmpty else { throw ClientError.message("分享为空、文字过长或附件超过 4 个。") }
        var coordinateError: NSError?, result: Error?
        NSFileCoordinator().coordinate(writingItemAt:packet, options:.forReplacing, error:&coordinateError) { target in
            do {
                guard !FileManager.default.fileExists(atPath:target.path) else { throw ClientError.message("还有一份分享等待处理，请先回 App 导入或清除。") }
                let files = try media.map { item -> SharedFile in
                    guard item.url.deletingLastPathComponent().standardizedFileURL == root.standardizedFileURL else { throw ClientError.message("分享文件位置无效。") }
                    return SharedFile(name:item.url.lastPathComponent, mime:item.mime, ext:item.ext)
                }
                let value = PendingShare(id:UUID(),owner:expected,text:text,files:files,created:Date())
                try JSONEncoder().encode(value).write(to:target,options:[.atomic,.completeFileProtection])
            } catch { result = error }
        }
        if let error = result ?? coordinateError { throw error }
    }
    func read(for expected: String) throws -> PendingShare? {
        guard FileManager.default.fileExists(atPath:packet.path) else { return nil }
        let attributes = try packet.resourceValues(forKeys:[.fileSizeKey,.isSymbolicLinkKey])
        guard attributes.isSymbolicLink != true, (attributes.fileSize ?? Int.max) <= 512 * 1024 else { throw ClientError.message("分享记录无效或过大。") }
        let data = try Data(contentsOf:packet)
        guard data.count <= 512 * 1024 else { throw ClientError.message("分享记录过大。") }
        let value = try JSONDecoder().decode(PendingShare.self,from:data)
        guard value.owner == expected, owner == expected, Date().timeIntervalSince(value.created) < 600, value.files.count <= 4 else {
            try acknowledge(value); throw ClientError.message("待处理分享已过期或不属于当前登录，请重新分享。")
        }
        return value
    }
    func file(_ value: SharedFile) throws -> URL {
        let name = value.name
        let u = URL(fileURLWithPath:name)
        guard !name.contains("/"), !name.contains("\\"), UUID(uuidString:u.deletingPathExtension().lastPathComponent) != nil,
              u.pathExtension == value.ext, MediaIO.formats[value.ext] == value.mime else { throw ClientError.message("分享文件标识无效。") }
        let path = root.appendingPathComponent(name)
        let attributes = try path.resourceValues(forKeys:[.isSymbolicLinkKey,.isRegularFileKey,.fileSizeKey])
        guard attributes.isSymbolicLink != true, attributes.isRegularFile == true, let size = attributes.fileSize, size > 0, size <= MediaIO.limit else { throw ClientError.message("分享附件无效或过大。") }
        return path
    }
    func acknowledge(_ value: PendingShare) throws {
        var error: NSError?, failure: Error?
        NSFileCoordinator().coordinate(writingItemAt:packet, options:.forDeleting,error:&error) { url in
            do {
                guard let bytes = try? Data(contentsOf:url), let current = try? JSONDecoder().decode(PendingShare.self,from:bytes), current.id == value.id else { return }
                for item in current.files { if let safe = try? file(item) { try? FileManager.default.removeItem(at:safe) } }
                try FileManager.default.removeItem(at:url)
            } catch { failure = error }
        }
        if let error = failure ?? error { throw error }
    }
    func clear() throws {
        var error: NSError?, failure: Error?
        NSFileCoordinator().coordinate(writingItemAt:packet,options:.forDeleting,error:&error) { url in
            do {
                for file in try FileManager.default.contentsOfDirectory(at:root,includingPropertiesForKeys:nil) {
                    if file.lastPathComponent == "pending.json" || (UUID(uuidString:file.deletingPathExtension().lastPathComponent) != nil && MediaIO.formats[file.pathExtension] != nil) { try FileManager.default.removeItem(at:file) }
                }
            } catch { failure = error }
        }
        if let error = failure ?? error { throw error }
    }
}
