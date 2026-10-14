import Foundation
import Security

struct Credentials: Codable { let server: String; let token: String }
enum CredentialStore {
    private static var query: [String:Any] { [kSecClass as String:kSecClassGenericPassword,kSecAttrService as String:"com.junshi.ios.session",kSecAttrAccount as String:"current"] }
    static func load() -> Credentials? {
        var q = query; q[kSecReturnData as String] = true; q[kSecMatchLimit as String] = kSecMatchLimitOne
        var value: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary,&value) == errSecSuccess, let bytes = value as? Data else { return nil }
        return try? JSONDecoder().decode(Credentials.self,from:bytes)
    }
    static func save(_ value: Credentials) throws {
        let data = try JSONEncoder().encode(value)
        let attributes: [String:Any] = [kSecValueData as String:data,kSecAttrAccessible as String:kSecAttrAccessibleWhenUnlockedThisDeviceOnly]
        let update = SecItemUpdate(query as CFDictionary,attributes as CFDictionary)
        if update == errSecItemNotFound {
            var q = query; attributes.forEach { q[$0.key] = $0.value }
            guard SecItemAdd(q as CFDictionary,nil) == errSecSuccess else { throw ClientError.message("无法保存登录凭证，请检查设备解锁状态。") }
        } else if update != errSecSuccess { throw ClientError.message("无法更新登录凭证。") }
    }
    static func clear() { SecItemDelete(query as CFDictionary) }
}
