#if DEBUG
import Foundation

// Explicit UI-test mode only. This file is absent from release behavior and
// never proxies to a real model account or skips real server authorization.
final class FixtureProtocol: URLProtocol {
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        let path = request.url!.path
        let value: Any
        if path.hasSuffix("/auth/login") { value = ["access_token":"synthetic-session"] }
        else if path.hasSuffix("/persons") { value = [["id":"p1","name":"测试人物","nickname":"小蓝"]] }
        else if path.hasSuffix("/conversations") && request.httpMethod == "POST" { value = ["id":"c2","title":"第二会话"] }
        else if path.hasSuffix("/conversations") { value = [["id":"c1","title":"测试会话"],["id":"c2","title":"第二会话"]] }
        else if path.hasSuffix("/platform-accounts") { value = [["id":"a1","platform":"wechat","account_handle":"synthetic","display_name":"测试微信"]] }
        else if path.hasSuffix("/platform-source") { value = ["id":"a1"] }
        else if path.hasSuffix("/strategic-reply/context") { value = ["draft":"刚忙完，正想找你聊聊。你呢？"] }
        else { value = ["status":"ok"] }
        let response = HTTPURLResponse(url:request.url!,statusCode:200,httpVersion:nil,headerFields:["Content-Type":"application/json"])!
        client?.urlProtocol(self,didReceive:response,cacheStoragePolicy:.notAllowed)
        client?.urlProtocol(self,didLoad:try! JSONSerialization.data(withJSONObject:value)); client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}
#endif
