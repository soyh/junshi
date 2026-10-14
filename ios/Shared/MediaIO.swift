import Foundation
import UniformTypeIdentifiers
import UIKit
import ImageIO

struct MediaItem: Identifiable, Equatable {
    let id: UUID; let url: URL; let mime: String; let ext: String
    init(url: URL, mime: String, ext: String) { id = UUID(); self.url = url; self.mime = mime; self.ext = ext }
}
enum MediaIO {
    static let limit = 50 * 1024 * 1024
    static let formats = ["jpg":"image/jpeg", "jpeg":"image/jpeg", "png":"image/png", "gif":"image/gif", "webp":"image/webp", "mp4":"video/mp4", "mov":"video/quicktime", "webm":"video/webm"]
    static func cache() throws -> URL {
        let root = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0].appendingPathComponent("JunshiImports", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root
    }
    static func copyBytes(_ source: URL, into output: FileHandle) throws {
        let input = try FileHandle(forReadingFrom: source); defer { try? input.close() }
        var total = 0
        while let bytes = try input.read(upToCount: 65536), !bytes.isEmpty {
            total += bytes.count
            guard total <= limit else { throw ClientError.message("每个附件最多 50 MB。") }
            try output.write(contentsOf: bytes)
        }
        guard total > 0 else { throw ClientError.message("附件为空。") }
    }
    static func importFile(_ source: URL, directory: URL? = nil, type: UTType? = nil) throws -> MediaItem {
        guard source.isFileURL else { throw ClientError.message("请选择系统提供的本地文件。") }
        let ext = source.pathExtension.lowercased()
        let kind = type ?? UTType(filenameExtension: ext)
        let root = try directory ?? cache()
        let output: URL; let mime: String; let outputExt: String
        if formats[ext] == nil, kind?.conforms(to: .image) == true {
            guard let image = CGImageSourceCreateWithURL(source as CFURL, nil),
                  let thumbnail = CGImageSourceCreateThumbnailAtIndex(image, 0, [kCGImageSourceCreateThumbnailFromImageAlways:true, kCGImageSourceThumbnailMaxPixelSize:2048, kCGImageSourceCreateThumbnailWithTransform:true] as CFDictionary),
                  let bytes = UIImage(cgImage: thumbnail).jpegData(compressionQuality: 0.9) else { throw ClientError.message("无法读取这张图片。") }
            outputExt = "jpg"; mime = "image/jpeg"; output = root.appendingPathComponent(UUID().uuidString + ".jpg")
            guard bytes.count <= limit else { throw ClientError.message("图片过大。") }
            try bytes.write(to: output, options: [.atomic, .completeFileProtection])
        } else {
            guard let format = formats[ext] else { throw ClientError.message("支持 JPG、PNG、GIF、WEBP、MP4、MOV、WEBM；其他图片会尝试转换。") }
            outputExt = ext; mime = format; output = root.appendingPathComponent(UUID().uuidString + "." + ext)
            FileManager.default.createFile(atPath: output.path, contents: nil, attributes: [.protectionKey: FileProtectionType.complete])
            do { let handle = try FileHandle(forWritingTo: output); defer { try? handle.close() }; try copyBytes(source, into: handle) }
            catch { try? FileManager.default.removeItem(at: output); throw error }
        }
        return MediaItem(url: output, mime: mime, ext: outputExt)
    }
    static func providerFile(_ provider: NSItemProvider, directory: URL? = nil) async throws -> MediaItem {
        guard let identifier = provider.registeredTypeIdentifiers.first(where: { UTType($0)?.conforms(to: .image) == true || UTType($0)?.conforms(to: .movie) == true }) else { throw ClientError.message("分享中没有可读取的图片或视频文件。") }
        return try await withCheckedThrowingContinuation { continuation in
            provider.loadFileRepresentation(forTypeIdentifier: identifier) { url, error in
                guard let url else { continuation.resume(throwing: error ?? ClientError.message("无法读取分享文件，请改用附件选择。")); return }
                do { continuation.resume(returning: try importFile(url, directory: directory, type: UTType(identifier))) }
                catch { continuation.resume(throwing: error) }
            }
        }
    }
    static func providerText(_ provider: NSItemProvider) async throws -> String {
        if provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
            return try await withCheckedThrowingContinuation { continuation in
                provider.loadItem(forTypeIdentifier: UTType.url.identifier, options: nil) { value, error in
                    if let url = value as? URL { continuation.resume(returning: url.absoluteString) }
                    else { continuation.resume(throwing: error ?? ClientError.message("无法读取分享链接。")) }
                }
            }
        }
        return try await withCheckedThrowingContinuation { continuation in
            provider.loadObject(ofClass: NSString.self) { value, error in
                if let value { continuation.resume(returning: String(describing: value)) }
                else { continuation.resume(throwing: error ?? ClientError.message("无法读取分享文字。")) }
            }
        }
    }
    static func remove(_ items: [MediaItem]) { for item in items { try? FileManager.default.removeItem(at: item.url) } }
}
