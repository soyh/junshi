import SwiftUI
import WebKit

struct WebTarget: Identifiable { let id = UUID(); let origin: URL; let ticket: String }
struct WebScreen: View {
    let target: WebTarget
    @Environment(\.dismiss) var dismiss
    var body: some View { NavigationStack { TrustedWeb(target:target).navigationTitle("主网页").navigationBarTitleDisplayMode(.inline).toolbar { Button("关闭") { dismiss() } } } }
}
struct TrustedWeb: UIViewRepresentable {
    let target: WebTarget
    final class Coordinator: NSObject, WKNavigationDelegate {
        let origin: URL
        init(_ origin: URL) { self.origin = origin }
        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = navigationAction.request.url, ServerPolicy.sameOrigin(origin,url) else { decisionHandler(.cancel); return }
            decisionHandler(.allow)
        }
    }
    func makeCoordinator() -> Coordinator { Coordinator(target.origin) }
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration(); config.websiteDataStore = .nonPersistent()
        let web = WKWebView(frame:.zero,configuration:config); web.navigationDelegate = context.coordinator
        let url = URL(string:target.origin.absoluteString+"/app#desktop-login="+target.ticket)!
        web.load(URLRequest(url:url)); return web
    }
    func updateUIView(_ uiView: WKWebView, context: Context) {}
    static func dismantleUIView(_ uiView: WKWebView, coordinator: Coordinator) { uiView.stopLoading(); uiView.navigationDelegate = nil; uiView.loadHTMLString("",baseURL:nil) }
}
