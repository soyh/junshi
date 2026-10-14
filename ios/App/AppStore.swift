import Foundation
import SwiftUI
import UniformTypeIdentifiers

@MainActor final class AppStore: ObservableObject {
    @Published var client: API?
    @Published var server = UserDefaults.standard.string(forKey:"server") ?? ""
    @Published var people: [Person] = []
    @Published var conversations: [Conversation] = []
    @Published var accounts: [PlatformAccount] = []
    @Published var profiles: [ModelProfile] = []
    @Published var person = ""
    @Published var conversation = ""
    @Published var account = ""
    @Published var input = ""
    @Published var draft = ""
    @Published var status = "登录后选择人物，再导入对方消息。"
    @Published var busy = false
    @Published var media: [MediaItem] = []
    @Published var sentAt = Date()
    @Published var web: WebTarget?
    private(set) var job: GenerateJob?
    private var epoch = 0
    private var newPerson: (name:String,title:String,id:String?,uncertain:Bool)?
    private let inbox = try? ShareInbox.configured()
    var owner: String? { client.flatMap { api in api.token.map { ShareInbox.fingerprint(server:api.origin.absoluteString,token:$0) } } }
    init() {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("-ui-testing") { CredentialStore.clear(); UserDefaults.standard.removeObject(forKey:"server"); server = ""; return }
        #endif
        if let c = CredentialStore.load(), let api = try? API(server:c.server,token:c.token) { client = api; server = c.server }
    }
    func run(_ message: String, action: @escaping () async throws -> Void) {
        guard !busy else { return }; busy = true; status = message; let version = epoch
        Task {
            defer { if version == epoch { busy = false } }
            do { try await action() }
            catch { if version == epoch { if case ClientError.unauthorized = error { logout(); status = "登录已失效，请重新登录。" } else { status = error.localizedDescription } } }
        }
    }
    func establish(_ api: API) async throws {
        guard let token = api.token, !token.isEmpty else { throw ClientError.message("服务器未返回登录凭证。") }
        let result: [Person] = try await api.decode("GET","/persons")
        try CredentialStore.save(Credentials(server:api.origin.absoluteString,token:token))
        people = result
        client = api; server = api.origin.absoluteString; UserDefaults.standard.set(server,forKey:"server")
        try? inbox?.bind(owner)
    }
    func logout() {
        let previous = client
        epoch += 1; client = nil; CredentialStore.clear(); busy = false
        people = []; conversations = []; accounts = []; profiles = []
        person = ""; conversation = ""; account = ""; input = ""; draft = ""; web = nil; job = nil; newPerson = nil
        MediaIO.remove(media); media = []; try? inbox?.bind(nil)
        status = "已退出登录。"
        if let previous { Task { _ = try? await previous.request("DELETE","/auth/session") } }
    }
    func loadPeople() {
        guard let api = client else { return }
        run("正在加载人物…") {
            let result: [Person] = try await api.decode("GET","/persons")
            guard self.client === api else { return }
            self.people = result; self.person = ""; self.conversation = ""; self.accounts = []; self.conversations = []
            try? self.inbox?.bind(self.owner); self.status = "请选择人物。可导入待处理的系统分享。"
        }
    }
    func selectPerson(_ id: String) {
        guard let api = client, !busy else { return }
        if !person.isEmpty && (!input.isEmpty || !media.isEmpty) { status = "请先清空本次输入，避免把内容放进另一位人物。"; return }
        run("正在加载会话与平台…") {
            let conversations: [Conversation] = try await api.decode("GET","/conversations?person_id="+id)
            let accounts: [PlatformAccount] = try await api.decode("GET","/persons/"+id+"/platform-accounts")
            guard self.client === api else { return }
            self.person = id; self.conversations = conversations; self.accounts = accounts; self.conversation = ""; self.account = ""; self.job = nil; self.draft = ""
            self.status = "请选择会话，再导入对方内容。"
        }
    }
    func selectConversation(_ id: String) {
        guard let api = client, !busy else { return }
        guard !id.isEmpty else { return }
        if !conversation.isEmpty && (!input.isEmpty || !media.isEmpty) { status = "请先清空本次输入，再切换会话。"; return }
        run("正在核对会话来源…") {
            let data = try await api.request("GET","/conversations/"+id+"/platform-source")
            let account = (try? JSONSerialization.jsonObject(with:data) as? [String:Any])?["id"] as? String ?? ""
            guard self.client === api else { return }
            self.conversation = id; self.account = account; self.job = nil; self.draft = ""; self.status = "已选择会话。"
        }
    }
    func clearDraft() { guard !busy else { return }; MediaIO.remove(media); media = []; input = ""; draft = ""; job = nil; sentAt = Date() }
    func changed() { if !busy { job = nil; draft = "" } }
    func jobChanged() { job = nil; draft = "" }
    func addFiles(_ urls: [URL]) {
        guard !busy else { return }
        run("正在准备附件…") {
            guard self.media.count + urls.count <= 4 else { throw ClientError.message("每次最多 4 个附件。") }
            var added: [MediaItem] = []
            do {
                for url in urls { let access = url.startAccessingSecurityScopedResource(); defer { if access { url.stopAccessingSecurityScopedResource() } }; added.append(try MediaIO.importFile(url)) }
            } catch { MediaIO.remove(added); throw error }
            self.media += added; self.job = nil; self.draft = ""; self.status = "附件已准备，尚未上传。"
        }
    }
    func pasteProviders(_ providers: [NSItemProvider]) {
        let version = epoch
        run("正在读取粘贴内容…") {
            guard self.input.isEmpty, self.media.isEmpty else { throw ClientError.message("请先清空当前草稿，再粘贴新的内容。") }
            var items: [MediaItem] = [], texts: [String] = []
            do {
                for provider in providers {
                    if provider.registeredTypeIdentifiers.contains(where:{ UTType($0)?.conforms(to:.image) == true || UTType($0)?.conforms(to:.movie) == true }) { guard items.count < 4 else { throw ClientError.message("每次最多 4 个附件。") }; items.append(try await MediaIO.providerFile(provider)) }
                    else { texts.append(try await MediaIO.providerText(provider)) }
                }
                guard self.epoch == version else { MediaIO.remove(items); return }
                self.input = texts.joined(separator:"\n"); self.media = items; self.job = nil; self.status = "已读取，确认人物与会话后再生成。"
            } catch { MediaIO.remove(items); throw error }
        }
    }
    func importShare() {
        run("正在读取待处理分享…") {
            guard let inbox = self.inbox, let owner = self.owner else { throw ClientError.message("分享入口需已配置 App Groups 签名并登录。") }
            guard self.input.isEmpty, self.media.isEmpty else { throw ClientError.message("先保存或清空本次草稿，再导入系统分享。") }
            guard let packet = try inbox.read(for:owner) else { throw ClientError.message("没有待处理分享。请在其他应用使用系统分享菜单。") }
            var items: [MediaItem] = []
            do { for file in packet.files { items.append(try MediaIO.importFile(inbox.file(file))) }; try inbox.acknowledge(packet) }
            catch { MediaIO.remove(items); throw error }
            self.input = packet.text; self.media = items; self.job = nil; self.status = "分享已导入，尚未上传。请确认人物、会话与内容。"
        }
    }
    func generate() {
        guard let api = client, !conversation.isEmpty else { status = "请先选择人物与会话。"; return }
        guard !input.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty || !media.isEmpty else { status = "请先输入文字或选择附件。"; return }
        guard input.unicodeScalars.count <= 100000 else { status = "本次文字过长，请分次导入。"; return }
        if job == nil { job = GenerateJob(person:person,conversation:conversation,text:input,sentAt:sentAt,media:media) }
        let current = job!
        run("正在保存内容并生成建议…") {
            let draft = try await current.generate(api)
            guard self.client === api else { return }
            self.draft = draft; self.status = "建议已生成。实际发送后再确认已发送。"
            Task { do { _ = try await api.request("POST","/persons/"+current.person+"/memory/refresh") } catch { if self.client === api, self.job === current { self.status = "建议已保留；档案更新未完成，可到主页面查看原因。" } } }
        }
    }
    func confirm() {
        guard let current = job, let api = client, !draft.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else { status = "请先生成有效建议。"; return }
        let text = draft
        run("正在登记已发送内容…") { try await current.confirm(api,reply:text); guard self.client === api else { return }; self.status = "已登记为我发送的消息。再次点击不会重复登记。" }
    }
    func createPerson(name: String, nickname: String, title: String, done: @escaping () -> Void) {
        guard let api = client else { return }
        run("正在创建人物与首个会话…") {
            guard !name.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty, !title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else { throw ClientError.message("请填写人物姓名与首个会话名称。") }
            if let attempt = self.newPerson, attempt.name != name || attempt.title != title { throw ClientError.message("上次创建结果尚未核对，请先刷新人物列表确认，不要更换信息重复创建。") }
            if self.newPerson == nil { self.newPerson = (name,title,nil,false) }
            if self.newPerson!.id == nil {
                guard !self.newPerson!.uncertain else { throw ClientError.message("上次人物创建结果不确定，请刷新主页面核对，避免重复创建。") }
                self.newPerson!.uncertain = true
                let result: Person = try await api.decode("POST","/persons",body:["name":name,"nickname":nickname])
                guard self.client === api else { return }
                self.newPerson!.id = result.id; self.newPerson!.uncertain = false
            }
            let id = self.newPerson!.id!
            var conversations: [Conversation] = try await api.decode("GET","/conversations?person_id="+id)
            guard self.client === api else { return }
            let conversation: Conversation
            if let existing = conversations.first(where:{$0.title == title}) { conversation = existing }
            else { conversation = try await api.decode("POST","/conversations",body:["person_id":id,"title":title]); conversations.append(conversation) }
            let people: [Person] = try await api.decode("GET","/persons")
            guard self.client === api else { return }
            self.people = people; self.person = id; self.conversations = conversations; self.conversation = conversation.id; self.accounts = []; self.account = ""; self.newPerson = nil
            self.status = "人物和首个会话已创建。"; done()
        }
    }
    func openWeb() {
        guard let api = client else { return }
        run("正在打开已登录主页面…") {
            let result: TicketResult = try await api.decode("POST","/auth/browser-handoff")
            guard result.ticket.range(of:"^[A-Za-z0-9_-]{43}$",options:.regularExpression) != nil else { throw ClientError.message("登录交接凭据无效。") }
            guard self.client === api else { return }
            self.web = WebTarget(origin:api.origin,ticket:result.ticket)
        }
    }
}
