import SwiftUI

@main @MainActor struct JunshiApp: App {
    @StateObject private var store = AppStore()
    var body: some Scene { WindowGroup { RootScreen().environmentObject(store) } }
}
