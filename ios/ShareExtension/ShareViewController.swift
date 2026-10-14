import UIKit
import UniformTypeIdentifiers

@MainActor final class ShareViewController: UIViewController {
    private let text = UITextView(), status = UILabel(), files = UILabel(), save = UIButton(type:.system)
    private var inbox: ShareInbox?, owner: String?, media: [MediaItem] = [], completed = false
    override func viewDidLoad() {
        super.viewDidLoad(); view.backgroundColor = UIColor(red:0.94,green:0.97,blue:1,alpha:1)
        let title = UILabel(); title.text = "分享到 AI 恋爱军师"; title.font = .preferredFont(forTextStyle:.headline)
        text.font = .preferredFont(forTextStyle:.body); text.layer.cornerRadius = 12; text.backgroundColor = .white
        status.numberOfLines = 0; status.font = .preferredFont(forTextStyle:.footnote); status.textColor = .secondaryLabel
        files.numberOfLines = 0; files.font = .preferredFont(forTextStyle:.caption1)
        save.setTitle("保存在 App 中继续",for:.normal); save.backgroundColor = .systemBlue; save.tintColor = .white; save.layer.cornerRadius = 12; save.isEnabled = false
        save.addTarget(self,action:#selector(saveShare),for:.touchUpInside)
        let cancel = UIButton(type:.system); cancel.setTitle("取消",for:.normal); cancel.addTarget(self,action:#selector(cancelShare),for:.touchUpInside)
        let stack = UIStackView(arrangedSubviews:[title,text,files,status,save,cancel]); stack.axis = .vertical; stack.spacing = 12; stack.translatesAutoresizingMaskIntoConstraints = false; view.addSubview(stack)
        NSLayoutConstraint.activate([stack.leadingAnchor.constraint(equalTo:view.safeAreaLayoutGuide.leadingAnchor,constant:20),stack.trailingAnchor.constraint(equalTo:view.safeAreaLayoutGuide.trailingAnchor,constant:-20),stack.topAnchor.constraint(equalTo:view.safeAreaLayoutGuide.topAnchor,constant:20),stack.bottomAnchor.constraint(lessThanOrEqualTo:view.safeAreaLayoutGuide.bottomAnchor,constant:-12),text.heightAnchor.constraint(equalToConstant:140),save.heightAnchor.constraint(equalToConstant:44)])
        preferredContentSize = CGSize(width:320,height:440)
        Task { await load() }
    }
    private func load() async {
        do {
            let inbox = try ShareInbox.configured(); self.inbox = inbox
            guard let owner = inbox.owner else { throw ClientError.message("请先打开 App 登录，再重新分享。") }; self.owner = owner
            guard try inbox.read(for:owner) == nil else { throw ClientError.message("还有待处理分享，请先在 App 导入或清除。") }
            var texts: [String] = []
            for item in extensionContext?.inputItems as? [NSExtensionItem] ?? [] {
                if let value = item.attributedContentText?.string, !value.isEmpty { texts.append(value) }
                for provider in item.attachments ?? [] {
                    if provider.registeredTypeIdentifiers.contains(where:{ UTType($0)?.conforms(to:.image) == true || UTType($0)?.conforms(to:.movie) == true }) {
                        guard media.count < 4 else { throw ClientError.message("每次最多 4 个附件，请分次分享。") }
                        media.append(try await MediaIO.providerFile(provider,directory:inbox.root))
                    } else if provider.canLoadObject(ofClass:NSString.self) || provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                        let value = try await MediaIO.providerText(provider); if !texts.contains(value) { texts.append(value) }
                    } else { throw ClientError.message("包含不支持的分享类型，请改用文字、图片或视频文件。") }
                }
            }
            guard !completed else { MediaIO.remove(media); media = []; return }
            text.text = texts.joined(separator:"\n"); files.text = media.isEmpty ? "没有媒体附件" : "已准备 \(media.count) 个附件"
            status.text = "这里只保存待处理内容，不会上传。完成后打开 App，选择人物与会话，再点“导入待处理分享”。分享链接不等于视频本体。"
            save.isEnabled = true
        } catch { MediaIO.remove(media); media = []; status.text = error.localizedDescription }
    }
    @objc private func saveShare() {
        do {
            guard let inbox, let owner else { throw ClientError.message("分享入口未准备完成。") }
            try inbox.save(text:text.text ?? "",media:media,owner:owner); completed = true
            extensionContext?.completeRequest(returningItems:[],completionHandler:nil)
        } catch { status.text = error.localizedDescription }
    }
    @objc private func cancelShare() { completed = true; MediaIO.remove(media); media = []; extensionContext?.cancelRequest(withError:NSError(domain:"JunshiShare",code:NSUserCancelledError)) }
}
