import assert from 'node:assert/strict';
import fs from 'node:fs';
import { JSDOM } from 'jsdom';

process.env.TZ = 'Asia/Shanghai';

const [mediaScriptPath] = process.argv.slice(2);
assert.ok(mediaScriptPath, 'expected exported media workspace script');

const mediaScript = fs.readFileSync(mediaScriptPath, 'utf8');

const dom = new JSDOM(`<!doctype html>
<html><body>
  <select id="conversation-select"><option value="conversation-1">conversation</option></select>
  <section id="conversation-content">
    <div class="workspace-grid">
      <section id="client-unified-import-card"></section>
    </div>
  </section>
</body></html>`, {
  runScripts: 'outside-only',
  url: 'http://127.0.0.1:18080/app',
});

const prelude = `
  const byId = (id) => document.getElementById(id);
  let currentAccessToken = 'test-token';
  let selectedConversationId = 'conversation-1';
  let currentMessageWindow = {};
  function requireToken() { return currentAccessToken; }
  async function api(path, options = {}) {
    if (path.includes('/analyze')) return {};
    if (path.includes('/media')) return [];
    return {};
  }
  async function loadMessages() {}
`;

dom.window.eval(`${prelude}\n${mediaScript}`);

const doc = dom.window.document;
const sentAtInput = doc.getElementById('client-media-sent-at');
assert.ok(sentAtInput, 'datetime input should be installed');
assert.equal(sentAtInput.type, 'datetime-local');
assert.equal(sentAtInput.step, '1');
assert.match(sentAtInput.value, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/);
assert.ok(sentAtInput.value.length > 0, 'datetime input should default to current local time');
assert.match(sentAtInput.title, /当前本地时间/);

const fixedLocal = new dom.window.Date(2026, 8, 22, 11, 30, 5);
assert.equal(
  dom.window.clientCurrentLocalDateTimeValue(fixedLocal),
  '2026-09-22T11:30:05',
);
assert.equal(
  dom.window.clientLocalDateTimeToIsoWithOffset('2026-09-22T11:30:00'),
  '2026-09-22T11:30:00+08:00',
);
assert.throws(
  () => dom.window.clientLocalDateTimeToIsoWithOffset('2026-09-31T11:30:00'),
  /证据时间无效/,
);

sentAtInput.value = '2026-09-22T11:30:00';
const fileInput = doc.getElementById('client-media-file');
const testFile = new dom.window.File(['image'], 'chat.png', {type: 'image/png'});
Object.defineProperty(fileInput, 'files', {value: [testFile], configurable: true});

let capturedForm = null;
dom.window.clientMediaApi = async (_path, options = {}) => {
  capturedForm = options.body;
  return {id: 'attachment-1'};
};

await dom.window.clientUploadAndAnalyzeMedia();

assert.ok(capturedForm instanceof dom.window.FormData);
assert.equal(capturedForm.get('sent_at'), '2026-09-22T11:30:00+08:00');
assert.match(sentAtInput.value, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/);
assert.notEqual(sentAtInput.value, '', 'successful upload must reset evidence time to current local time');

console.log('TEST-194 media evidence datetime-local runtime: PASS');
