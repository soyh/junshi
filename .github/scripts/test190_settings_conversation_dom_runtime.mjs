import assert from 'node:assert/strict';
import fs from 'node:fs';
import { JSDOM } from 'jsdom';

const [settingsPath, compactPath] = process.argv.slice(2);
assert.ok(settingsPath && compactPath, 'expected exported workspace scripts');

const settingsScript = fs.readFileSync(settingsPath, 'utf8');
const compactScript = fs.readFileSync(compactPath, 'utf8');

const dom = new JSDOM(`<!doctype html>
<html><body>
  <div id="client-settings-host">
    <details id="guided-settings" open>
      <summary tabindex="0">账号、安全与模型设置</summary>
      <div id="guided-settings-content">
        <details class="lifecycle-settings-panel">
          <summary>账号登录</summary>
          <fieldset id="account"><legend>账号</legend></fieldset>
        </details>
        <details class="lifecycle-settings-panel">
          <summary>Session management</summary>
          <fieldset><legend>Sessions</legend></fieldset>
        </details>
        <details class="lifecycle-settings-panel">
          <summary>Account Security</summary>
          <fieldset id="account-security"><legend>Security</legend></fieldset>
        </details>
        <details class="lifecycle-settings-panel">
          <summary>LLM 模型设置</summary>
          <fieldset id="provider"><legend>LLM Provider</legend></fieldset>
        </details>
      </div>
    </details>
  </div>

  <div id="client-conversation-host">
    <select id="conversation-select">
      <option value="c1" data-test166-base-label="过去记录 · active">1 · 过去记录 · active</option>
      <option value="c2" data-test166-base-label="第二段记录 · archived">2 · 第二段记录 · archived</option>
    </select>
    <div id="conversation-content"></div>
  </div>
</body></html>`, {
  runScripts: 'outside-only',
  url: 'http://127.0.0.1:18080/app',
});

const prelude = `
  const byId = (id) => document.getElementById(id);
  let currentAccessToken = 'test-token';
  let selectedPersonId = 'person-1';
  let selectedConversationId = 'c1';
  async function loadConversations() {}
  async function loadMessages() {}
  async function createConversation() {}
`;

dom.window.eval(`${prelude}\n${settingsScript}\n${compactScript}`);

const doc = dom.window.document;

const tabs = Array.from(doc.querySelectorAll('#guided-settings-tabs .settings-tab-button'));
assert.equal(tabs.length, 4);
assert.deepEqual(
  tabs.map((tab) => tab.textContent),
  ['账号登录', '登录会话', '账号安全', '模型设置'],
);
assert.equal(doc.getElementById('provider')?.parentElement?.id, 'guided-settings-panel-host');

const chips = Array.from(doc.querySelectorAll('.client-conversation-chip'));
assert.equal(chips.length, 2);
assert.equal(chips[0].querySelector('.client-conversation-chip-label')?.textContent, '过去记录');
assert.equal(chips[0].querySelector('.client-conversation-chip-state')?.textContent, '当前');
assert.equal(chips[0].getAttribute('aria-selected'), 'true');
assert.match(chips[0].title, /当前会话：过去记录/);
assert.ok(!chips[0].textContent.includes('active'));

assert.equal(chips[1].querySelector('.client-conversation-chip-label')?.textContent, '第二段记录');
assert.equal(chips[1].querySelector('.client-conversation-chip-state'), null);
assert.equal(chips[1].getAttribute('aria-selected'), 'false');
assert.ok(!chips[1].textContent.includes('archived'));

const settingsDetails = doc.getElementById('guided-settings');
assert.equal(settingsDetails?.open, true);

console.log('TEST-190 browser-like settings/conversation DOM runtime: PASS');
