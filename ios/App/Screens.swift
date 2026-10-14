import SwiftUI
import PhotosUI
import CoreTransferable
import UniformTypeIdentifiers

struct ImportedPhoto: Transferable {
    let item: MediaItem
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(importedContentType:.image) { value in ImportedPhoto(item:try MediaIO.importFile(value.file,type:.image)) }
        FileRepresentation(importedContentType:.movie) { value in ImportedPhoto(item:try MediaIO.importFile(value.file,type:.movie)) }
    }
}
struct Panel<Content: View>: View {
    let title: String; let content: Content
    init(_ title: String, @ViewBuilder content: () -> Content) { self.title = title; self.content = content() }
    var body: some View {
        VStack(alignment:.leading,spacing:12) { Text(title).font(.headline); content }
            .frame(maxWidth:.infinity,alignment:.leading).padding(18)
            .background(.white,in:RoundedRectangle(cornerRadius:20))
            .overlay(RoundedRectangle(cornerRadius:20).stroke(Color.blue.opacity(0.12)))
            .shadow(color:.blue.opacity(0.07),radius:12,y:5)
    }
}
struct RootScreen: View {
    @EnvironmentObject var store: AppStore
    var body: some View {
        NavigationStack {
            Group {
                if store.client == nil { LoginScreen() }
                else if store.person.isEmpty { PeopleScreen() }
                else { WorkspaceScreen() }
            }.background(Color(red:0.94,green:0.97,blue:1)).tint(Color(red:0.16,green:0.48,blue:0.76))
        }.sheet(item:$store.web) { value in WebScreen(target:value) }
        .task { if store.client != nil { store.loadPeople() } }
    }
}
struct LoginScreen: View {
    @EnvironmentObject var store: AppStore
    @State private var mode = "login", username = "", password = "", email = "", code = ""
    @State private var challenge: (id:String,email:String,purpose:String,server:String)?
    var body: some View {
        ScrollView {
            VStack(spacing:18) {
                Image(systemName:"bubble.left.and.bubble.right.fill").font(.system(size:44)).foregroundStyle(.blue).padding(.top,25)
                Text("AI 恋爱军师").font(.largeTitle.bold())
                Text("同一份人物档案，陪你把对话接下去。").foregroundStyle(.secondary)
                Panel("连接与账号") {
                    TextField("HTTPS 服务器地址",text:$store.server).textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL).accessibilityIdentifier("server")
                    Picker("操作",selection:$mode) { Text("登录").tag("login"); Text("注册").tag("register"); Text("找回密码").tag("reset") }.pickerStyle(.segmented)
                    if mode != "reset" { TextField("软件账号",text:$username).textInputAutocapitalization(.never).autocorrectionDisabled().accessibilityIdentifier("username") }
                    SecureField(mode == "reset" ? "新密码" : "密码",text:$password).accessibilityIdentifier("password")
                    if mode != "login" {
                        Text("账号 3–64 位：字母、数字、. _ -。密码 12–256 个字符，无强制特殊符号。").font(.caption).foregroundStyle(.secondary)
                        TextField("邮箱",text:$email).textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.emailAddress)
                        HStack { TextField("六位验证码",text:$code).keyboardType(.numberPad); Button("发送验证码",action:sendCode).buttonStyle(.bordered) }
                        Text("验证码 10 分钟有效；注册使用服务器的邮箱验证流程。").font(.caption).foregroundStyle(.secondary)
                    }
                    Button(mode == "login" ? "登录" : mode == "register" ? "验证并注册" : "重置密码",action:submit).buttonStyle(.borderedProminent).frame(maxWidth:.infinity).accessibilityIdentifier("login-submit")
                }.disabled(store.busy)
                if store.busy { ProgressView() }
                Text(store.status).font(.callout).foregroundStyle(.secondary).accessibilityIdentifier("status")
                Text("业务数据保存在你的服务器；每个账号独立配置模型 API。").font(.caption).foregroundStyle(.secondary)
            }.padding(20)
        }.onChange(of:mode) { _,_ in challenge = nil; code = ""; password = "" }
        .onChange(of:email) { _,_ in challenge = nil }
        .onChange(of:store.server) { _,_ in challenge = nil }
    }
    private func sendCode() {
        let address = email.trimmingCharacters(in:.whitespacesAndNewlines), purpose = mode, server = store.server
        store.run("正在发送验证码…") {
            let api = try API(server:server)
            let value: ChallengeResult = try await api.decode("POST","/auth/email/code",body:["email":address,"purpose":purpose])
            guard self.mode == purpose, self.email.trimmingCharacters(in:.whitespacesAndNewlines) == address, self.store.server == server else { return }
            self.challenge = (value.challenge_id,address,purpose,server); self.store.status = value.message
        }
    }
    private func submit() {
        let name = username.trimmingCharacters(in:.whitespacesAndNewlines), pass = password, currentMode = mode, address = email.trimmingCharacters(in:.whitespacesAndNewlines)
        store.run("正在验证账号…") {
            let api = try API(server:store.server)
            if currentMode == "login" {
                let result: LoginResult = try await api.decode("POST","/auth/login",body:["username":name,"password":pass])
                try store.establish(API(server:api.origin.absoluteString,token:result.access_token)); password = ""; store.status = "登录成功。"
            } else {
                try Registration.validate(currentMode == "reset" ? "reset-user" : name,pass)
                guard let challenge, challenge.email == address, challenge.purpose == currentMode, challenge.server == store.server else { throw ClientError.message("请先发送本次操作的验证码。") }
                var body: [String:Any] = ["email":address,"challenge_id":challenge.id,"code":code]
                if currentMode == "register" {
                    body["username"] = name; body["password"] = pass
                    let result: LoginResult = try await api.decode("POST","/auth/email/register",body:body)
                    try store.establish(API(server:api.origin.absoluteString,token:result.access_token)); password = ""; code = ""; store.status = "注册成功。"
                } else { body["new_password"] = pass; _ = try await api.request("POST","/auth/email/reset-password",body:body); password = ""; code = ""; self.challenge = nil; mode = "login"; store.status = "密码已重置，请重新登录。" }
            }
        }
    }
}
struct PeopleScreen: View {
    @EnvironmentObject var store: AppStore
    @State private var create = false, models = false
    let columns = [GridItem(.adaptive(minimum:150),spacing:15)]
    var body: some View {
        ScrollView {
            VStack(spacing:18) {
                Text("选择一位人物，继续你们的故事。").foregroundStyle(.secondary)
                LazyVGrid(columns:columns,spacing:15) {
                    ForEach(store.people) { person in
                        Button { store.selectPerson(person.id) } label: {
                            VStack(alignment:.leading,spacing:16) { Text(String(person.name.prefix(1))).font(.system(size:36,weight:.bold)).foregroundStyle(.blue); Text(person.nickname?.isEmpty == false ? "\(person.name)（\(person.nickname!)）" : person.name).font(.headline); Text("进入人物工作区").font(.caption).foregroundStyle(.secondary) }.frame(maxWidth:.infinity,minHeight:145,alignment:.leading).padding(18).background(.white,in:RoundedRectangle(cornerRadius:22)).shadow(color:.blue.opacity(0.10),radius:12,y:6)
                        }.buttonStyle(.plain).accessibilityIdentifier("person-"+person.id)
                    }
                }
                Button("新建人物与首个会话") { create = true }.buttonStyle(.borderedProminent)
                HStack { Button("刷新人物") { store.loadPeople() }; Button("模型设置") { models = true }; Button("主网页 / 账号管理") { store.openWeb() } }.font(.footnote)
                Button("导入待处理分享") { store.importShare() }.buttonStyle(.bordered)
                if store.busy { ProgressView() }
                Text(store.status).font(.callout).foregroundStyle(.secondary).accessibilityIdentifier("status")
            }.padding(20)
        }.navigationTitle("AI 恋爱军师").toolbar { Button("退出登录") { store.logout() } }
        .disabled(store.busy)
        .task { if store.people.isEmpty { store.loadPeople() } }
        .sheet(isPresented:$create) { NewPersonScreen() }.sheet(isPresented:$models) { ModelScreen() }
    }
}
struct WorkspaceScreen: View {
    @EnvironmentObject var store: AppStore
    @State private var files = false, platform = false, showBack = false
    @State private var photos: [PhotosPickerItem] = []
    @FocusState private var editing: Bool
    private var title: String { store.people.first(where:{$0.id == store.person})?.name ?? "人物工作区" }
    var body: some View {
        ScrollView {
            VStack(spacing:16) {
                Panel("本次对话") {
                    Picker("会话",selection:Binding(get:{store.conversation},set:{store.selectConversation($0)})) { Text("请选择会话").tag(""); ForEach(store.conversations) { Text($0.title ?? "未命名会话").tag($0.id) } }.accessibilityIdentifier("conversation-picker")
                    Text(store.accounts.first(where:{$0.id == store.account})?.label ?? "平台来源：未标注").font(.caption).foregroundStyle(.secondary)
                    HStack { Button("新建平台账号") { platform = true }; Button("主网页 / 完整档案") { store.openWeb() } }.font(.footnote)
                }
                Panel("对方的回复 / 待导入内容") {
                    TextEditor(text:$store.input).frame(minHeight:110).focused($editing).accessibilityIdentifier("incoming-text")
                    DatePicker("发送时间（北京时间）",selection:$store.sentAt).environment(\.locale,Locale(identifier:"zh_CN")).environment(\.timeZone,TimeZone(secondsFromGMT:28800)!)
                    HStack { PasteButton(supportedContentTypes:[.plainText,.image,.movie,.url]) { store.pasteProviders($0) }.labelStyle(.titleOnly); Button("文件") { files = true }; PhotosPicker(selection:$photos,maxSelectionCount:4,matching:.any(of:[.images,.videos])) { Text("照片 / 视频") } }.buttonStyle(.bordered).font(.footnote)
                    Button("导入待处理分享") { store.importShare() }.font(.footnote)
                    ForEach(store.media) { item in HStack { Image(systemName:item.mime.hasPrefix("video") ? "video" : "photo"); Text(item.url.lastPathComponent).font(.caption).lineLimit(1); Spacer(); Button("移除") { MediaIO.remove([item]); store.media.removeAll(where:{$0.id == item.id}); store.changed() } } }
                    Text("每次最多 4 个附件，每个最多 50 MB。输入不会自动发给对方；生成时才上传到你的服务器。").font(.caption).foregroundStyle(.secondary)
                    HStack { Button("生成回复建议") { store.generate() }.buttonStyle(.borderedProminent).accessibilityIdentifier("generate"); Button("清空本次内容") { store.clearDraft() }.buttonStyle(.bordered) }
                }.disabled(store.busy)
                Panel("建议回复") {
                    TextEditor(text:$store.draft).frame(minHeight:100).accessibilityIdentifier("reply-draft")
                    HStack { Button("一键复制") { UIPasteboard.general.string = store.draft; store.status = "已复制。实际发送后再确认已发送。" }.buttonStyle(.bordered).disabled(store.draft.isEmpty); Button("确认已发送") { store.confirm() }.buttonStyle(.borderedProminent).disabled(store.draft.isEmpty).accessibilityIdentifier("confirm-sent") }
                    Text("这里的确认只登记你已发送的内容，不会接管微信等应用发送消息。").font(.caption).foregroundStyle(.secondary)
                }.disabled(store.busy)
                if store.busy { ProgressView() }
                Text(store.status).font(.callout).foregroundStyle(.secondary).accessibilityIdentifier("status")
            }.padding(18)
        }.navigationTitle(title).toolbar {
            ToolbarItemGroup(placement:.keyboard) { Spacer(); Button("完成") { editing = false } }
            ToolbarItem(placement:.topBarLeading) { Button("返回人物") { if !store.input.isEmpty || !store.media.isEmpty || !store.draft.isEmpty { showBack = true } else { store.person = ""; store.conversation = "" } }.disabled(store.busy) }
        }.confirmationDialog("返回人物会清空本机未提交草稿，服务器已保存的记录保留。",isPresented:$showBack,titleVisibility:.visible) { Button("清空并返回",role:.destructive) { store.clearDraft(); store.person = ""; store.conversation = "" } }
        .sheet(isPresented:$platform) { PlatformScreen() }
        .fileImporter(isPresented:$files,allowedContentTypes:[.image,.movie],allowsMultipleSelection:true) { result in switch result { case .success(let urls): store.addFiles(urls); case .failure(let error): store.status = error.localizedDescription } }
        .onChange(of:store.input) { _,_ in store.changed() }.onChange(of:store.sentAt) { _,_ in store.changed() }
        .onChange(of:photos) { _,items in
            guard !items.isEmpty else { return }
            store.run("正在读取照片与视频…") {
                let api = store.client; var added: [MediaItem] = []
                do {
                    guard store.media.count + items.count <= 4 else { throw ClientError.message("每次最多 4 个附件。") }
                    for item in items { guard let file = try await item.loadTransferable(type:ImportedPhoto.self) else { throw ClientError.message("附件无法读取。"); }; added.append(file.item) }
                    guard store.client === api else { MediaIO.remove(added); return }
                    store.media += added; store.jobChanged(); photos = []; store.status = "附件已准备，尚未上传。"
                } catch { MediaIO.remove(added); throw error }
            }
        }
    }
}
struct NewPersonScreen: View {
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) var dismiss
    @State private var name = "", nickname = "", title = ""
    var body: some View {
        NavigationStack { Form { TextField("人物姓名",text:$name); TextField("昵称（可选）",text:$nickname); TextField("首个会话名称",text:$title); Text("创建人物时同时创建首个会话，名称由你填写。").font(.caption); Button("创建人物与会话") { store.createPerson(name:name,nickname:nickname,title:title) { dismiss() } }; Text(store.status) }.disabled(store.busy).navigationTitle("新建人物").toolbar { Button("关闭") { dismiss() }.disabled(store.busy) } }
    }
}
struct PlatformScreen: View {
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) var dismiss
    @State private var platform = "wechat", handle = "", display = "", bind = true, uncertain = false
    var body: some View {
        NavigationStack { Form {
            Picker("平台",selection:$platform) { Text("微信").tag("wechat"); Text("抖音").tag("douyin"); Text("探探").tag("tantan"); Text("陌陌").tag("momo"); Text("Soul").tag("soul"); Text("其他").tag("other") }
            TextField("平台账号标识",text:$handle); TextField("显示名称（可选）",text:$display)
            if !store.conversation.isEmpty { Toggle("标注为当前会话来源",isOn:$bind) }
            Button("保存平台账号") { save() }; Text(store.status)
        }.disabled(store.busy).navigationTitle("同一人物的多个平台账号").toolbar { Button("关闭") { dismiss() }.disabled(store.busy) } }
    }
    private func save() {
        guard let api = store.client else { return }; let person = store.person, conversation = store.conversation
        store.run("正在保存平台账号…") {
            guard !handle.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else { throw ClientError.message("请填写平台账号标识。") }
            guard !uncertain else { throw ClientError.message("上次创建结果不确定，请到主网页核对平台列表后再操作。") }; uncertain = true
            let result: PlatformAccount = try await api.decode("POST","/persons/"+person+"/platform-accounts",body:["platform":platform,"account_handle":handle,"display_name":display])
            if bind && !conversation.isEmpty { _ = try await api.request("PUT","/conversations/"+conversation+"/platform-source",body:["account_id":result.id]) }
            let accounts: [PlatformAccount] = try await api.decode("GET","/persons/"+person+"/platform-accounts")
            guard store.client === api else { return }; store.accounts = accounts; if bind { store.account = result.id }; store.status = "平台账号已保存。"; dismiss()
        }
    }
}
struct ModelScreen: View {
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) var dismiss
    @State private var name = "", provider = "qwen", endpoint = "", model = "", key = ""
    var body: some View {
        NavigationStack { Form {
            Section("当前用户的配置") { ForEach(store.profiles) { profile in VStack(alignment:.leading) { Text(profile.name + (profile.is_active ? " · 当前" : "")); Text(profile.provider+" / "+profile.model).font(.caption); HStack { Button("启用") { action(profile.id,"activate") }; Button("测试连接") { action(profile.id,"test") } } } } }
            Section("新增配置并启用") {
                TextField("配置名称",text:$name)
                Picker("供应商",selection:$provider) { ForEach(["qwen","deepseek","kimi","openai","gemini","openai_compatible"],id:\.self) { Text($0).tag($0) } }
                TextField("供应商 API 地址",text:$endpoint).textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                TextField("模型名称",text:$model).textInputAutocapitalization(.never).autocorrectionDisabled()
                SecureField("你自己的 API Key",text:$key)
                Text("密钥仅提交给你的服务器；不会回显、写入分享缓存或与其他用户共用。完整编辑与视觉模型选择可在主网页设置中进行。").font(.caption)
                Button("保存并启用") { save() }
            }
            Text(store.status)
        }.disabled(store.busy).navigationTitle("模型设置").toolbar { Button("关闭") { key = ""; dismiss() }.disabled(store.busy) }.task { reload() }.onDisappear { key = "" } }
    }
    private func reload() {
        guard let api = store.client else { return }
        store.run("正在加载模型配置…") { let result: [ModelProfile] = try await api.decode("GET","/settings/llm/profiles"); guard store.client === api else { return }; store.profiles = result; store.status = "配置只属于当前账号。" }
    }
    private func action(_ id: String, _ operation: String) {
        guard let api = store.client else { return }
        store.run("正在处理模型配置…") { _ = try await api.request("POST","/settings/llm/profiles/"+id+"/"+operation); let result: [ModelProfile] = try await api.decode("GET","/settings/llm/profiles"); guard store.client === api else { return }; store.profiles = result; store.status = "操作成功。" }
    }
    private func save() {
        guard let api = store.client else { return }
        store.run("正在保存当前用户的配置…") {
            guard !name.isEmpty, !model.isEmpty, !key.isEmpty else { throw ClientError.message("请填写名称、模型和 API Key。") }
            guard let url = URLComponents(string:endpoint), let scheme = url.scheme, ["https","http"].contains(scheme), url.host != nil, url.user == nil, url.password == nil, url.query == nil, url.fragment == nil else { throw ClientError.message("模型接口地址无效。") }
            _ = try await api.request("POST","/settings/llm/profiles",body:["name":name,"provider":provider,"base_url":endpoint,"model":model,"api_key":key,"timeout_seconds":60,"activate":true]); key = ""
            let result: [ModelProfile] = try await api.decode("GET","/settings/llm/profiles"); guard store.client === api else { return }; store.profiles = result; store.status = "已保存并启用，请测试连接。"
        }
    }
}
