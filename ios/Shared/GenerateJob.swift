import Foundation

@MainActor final class GenerateJob {
    let person: String, conversation: String, text: String, sentAt: String
    let media: [MediaItem]
    let messageID = UUID().uuidString, confirmID = UUID().uuidString
    private let uploadIDs: [String]
    private var uploaded: [Int:String] = [:], analyzed: Set<Int> = []
    private var saved = false
    private(set) var confirmed = false
    private var confirmedText: String?, confirmedTime: String?
    init(person: String, conversation: String, text: String, sentAt: Date, media: [MediaItem]) {
        self.person = person; self.conversation = conversation; self.text = text; self.sentAt = ChinaTime.timestamp(sentAt); self.media = media
        uploadIDs = media.map { _ in UUID().uuidString }
    }
    func generate(_ api: APITransport) async throws -> String {
        guard !confirmed else { throw ClientError.message("本次回复已经登记，请清空或输入新的对方消息。") }
        if !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !saved {
            _ = try await api.request("POST", "/pc/messages", body: ["operation_id":messageID, "conversation_id":conversation, "sender_type":"person", "content":text, "sent_at":sentAt]); saved = true
        }
        for i in media.indices {
            if uploaded[i] == nil {
                let result = try await api.upload("/pc/conversations/\(conversation)/media", item:media[i], operation:uploadIDs[i], sentAt:sentAt)
                uploaded[i] = try JSONDecoder().decode(IDResult.self, from:result).id
            }
            if !analyzed.contains(i) {
                _ = try await api.request("POST", "/media/\(uploaded[i]!)/analyze", body:nil); analyzed.insert(i)
            }
        }
        let result: ReplyResult = try await api.decode("GET", "/conversations/\(conversation)/strategic-reply/context")
        guard let draft = result.draft, !draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw ClientError.message("未返回有效建议。记录已保存，保持本次输入重试即可。") }
        return draft
    }
    func confirm(_ api: APITransport, reply: String) async throws {
        guard !confirmed else { return }
        if let previous = confirmedText, previous != reply { throw ClientError.message("上次确认结果不确定，请保留同一回复重试或先在主页面核对。") }
        if confirmedText == nil { confirmedText = reply; confirmedTime = ChinaTime.timestamp(Date()) }
        _ = try await api.request("POST", "/pc/messages", body:["operation_id":confirmID, "conversation_id":conversation, "sender_type":"user", "content":reply, "sent_at":confirmedTime!])
        confirmed = true
    }
}
