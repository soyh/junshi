import assert from 'node:assert/strict';
import fs from 'node:fs';
import { JSDOM } from 'jsdom';

const [settingsPath, multiPath, dualPath] = process.argv.slice(2);
assert.ok(settingsPath && multiPath && dualPath, 'expected exported workspace scripts');

const settingsScript = fs.readFileSync(settingsPath, 'utf8');
const multiScript = fs.readFileSync(multiPath, 'utf8');
const dualScript = fs.readFileSync(dualPath, 'utf8');

const dom = new JSDOM(`<!doctype html>
<html><body>
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
      <fieldset id="provider" class="wide">
        <legend>LLM Provider</legend>
        <label for="provider-name">模型接口类型</label>
        <select id="provider-name"><option value="openai_compatible">OpenAI-compatible</option></select>
        <label for="base-url">接口地址</label>
        <input id="base-url" />
        <label for="model">模型名称</label>
        <input id="model" />
        <label for="api-key">API Key</label>
        <input id="api-key" />
        <label for="timeout">超时时间</label>
        <input id="timeout" value="60" />
        <button id="load-provider" type="button">读取配置</button>
        <button id="save-provider" type="button">保存配置</button>
        <button id="test-provider" type="button">测试连接</button>
        <button id="delete-provider" type="button">删除配置</button>
        <div id="provider-status"></div>
      </fieldset>
    </details>
  </div>
</body></html>`, {
  runScripts: 'outside-only',
  url: 'http://127.0.0.1:18080/app',
});

const prelude = `
  const byId = (id) => document.getElementById(id);
  let currentAccessToken = null;
  const providerStatus = byId('provider-status');
  let establishSession = function establishSession() {};
  async function api() { throw new Error('API should not be called while logged out'); }
`;

dom.window.eval(`${prelude}\n${settingsScript}\n${multiScript}\n${dualScript}`);

const doc = dom.window.document;
const provider = doc.getElementById('provider');
assert.ok(provider, 'provider mount point must survive settings-tab installation');
assert.equal(provider.parentElement?.id, 'guided-settings-panel-host');
assert.equal(doc.querySelectorAll('#provider').length, 1);

const providerTab = doc.querySelector('[role="tab"][aria-controls="provider"]');
assert.ok(providerTab, 'provider tab must continue targeting the stable provider id');

const settings = doc.getElementById('guided-settings-content');
assert.equal(settings?.dataset.sharedTabsInstalled, 'true');

const dualGrid = doc.getElementById('dual-model-settings');
const primaryCard = doc.getElementById('dual-primary-card');
const visionCard = doc.getElementById('dual-vision-card');
assert.ok(dualGrid, 'dual-model settings grid must be installed at runtime');
assert.ok(primaryCard, 'primary model card must be installed at runtime');
assert.ok(visionCard, 'vision model card must be installed at runtime');

assert.match(primaryCard.textContent, /主文本 \/ 分析模型/);
assert.match(visionCard.textContent, /视觉 \/ 图片视频模型/);
assert.match(primaryCard.textContent, /TEXT · 主路由/);
assert.match(visionCard.textContent, /VISION · 多模态/);

assert.equal(doc.getElementById('dual-primary-state')?.textContent, '等待登录');
assert.equal(doc.getElementById('dual-vision-state')?.textContent, '等待登录');

const advanced = doc.getElementById('provider-advanced-profiles');
const advancedContent = doc.getElementById('provider-advanced-profiles-content');
assert.ok(advanced, 'advanced compatibility settings must remain available');
assert.ok(advancedContent?.contains(doc.getElementById('provider-name')));
assert.ok(advanced.textContent.includes('高级：Profile 管理与兼容设置'));

assert.ok(doc.getElementById('dual-primary-provider'));
assert.ok(doc.getElementById('dual-primary-model'));
assert.ok(doc.getElementById('dual-primary-base-url'));
assert.ok(doc.getElementById('dual-primary-api-key'));
assert.ok(doc.getElementById('dual-vision-provider'));
assert.ok(doc.getElementById('dual-vision-model'));
assert.ok(doc.getElementById('dual-vision-base-url'));
assert.ok(doc.getElementById('dual-vision-api-key'));

console.log('TEST-189 browser-like dual-model DOM mount: PASS');
