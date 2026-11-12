import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'docs');
const source = readFileSync(path.join(root, 'app.js'), 'utf8');
for (const page of ['index.html', 'zh.html', 'guide.html', 'guide-zh.html']) {
 const html = readFileSync(path.join(root, page), 'utf8');
 const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
 assert.equal(new Set(ids).size, ids.length, `${page}: duplicate ids`);
 for (const [, href] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
  if (href.startsWith('#')) { if (href.length > 1) assert.ok(ids.includes(href.slice(1)), `${page}: missing anchor ${href}`); }
  else if (!href.startsWith('https://')) {
   const [resource, fragment] = href.split('#');
   const destination = path.join(root, resource.split('?')[0]);
   assert.ok(existsSync(destination), `${page}: missing asset ${href}`);
   if (fragment) {
    const destinationIds = [...readFileSync(destination, 'utf8').matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
    assert.ok(destinationIds.includes(fragment), `${page}: missing destination anchor ${href}`);
   }
  }
 }
 assert.match(html, /hreflang="zh-CN"/);
 assert.match(html, /hreflang="en"/);
 assert.match(html, /aria-live="polite"/);
}

function element() {
 return { textContent: '', className: '', attrs: {}, events: {}, classList: { toggle() {} },
  setAttribute(key, value) { this.attrs[key] = value; },
  getAttribute(key) { return this.attrs[key]; },
  addEventListener(key, callback) { this.events[key] = callback; } };
}
function start({ lang = 'en', url = 'https://example.test/phoenix/', remembered = null, browser = 'en-US', blocked = false } = {}) {
 const ids = ['command', 'copy-command', 'copy-status', 'demo-kicker', 'demo-title', 'demo-verdict', 'execution', 'freshness', 'demo-output', 'demo-explanation'];
 const nodes = Object.fromEntries(ids.map(id => [id, element()]));
 nodes.command.textContent = 'python -B -m phoenix_continuity_gate demo-record';
 const steps = Array.from({ length: 4 }, element);
 const switcher = element(); switcher.attrs.href = lang === 'en' ? 'zh.html?lang=zh' : 'index.html?lang=en';
 const location = { href: url, hash: new URL(url).hash, replace(value) { this.redirect = value; } };
 const storage = { value: remembered, getItem() { if (blocked) throw Error('denied'); return this.value; }, setItem(key, value) { if (blocked) throw Error('denied'); this.value = value; } };
 const clipboard = { async writeText(value) { this.copied = value; } };
 vm.runInNewContext(source, { URL, window: { location, localStorage: storage }, navigator: { language: browser, clipboard },
  document: { documentElement: { lang }, querySelectorAll: selector => selector === '.step' ? steps : [switcher], getElementById: id => nodes[id] } });
 return { nodes, steps, location, storage, clipboard, switcher };
}
const outcomes = [['SUCCEEDED', 'MATCH', 'PASS'], ['SUCCEEDED', 'CHANGED', 'BLOCK'], ['FAILED', 'MATCH', 'BLOCK'], ['SUCCEEDED', 'MATCH', 'PASS']];
for (const lang of ['en', 'zh-CN']) {
 const session = start({ lang, url: `https://example.test/phoenix/${lang === 'en' ? 'index.html?lang=en' : 'zh.html'}` });
 assert.equal(session.location.redirect, undefined);
 for (let i = 0; i < 4; i++) {
  session.steps[i].events.click();
  assert.deepEqual([session.nodes.execution.textContent, session.nodes.freshness.textContent, session.nodes['demo-verdict'].textContent], outcomes[i]);
  session.steps.forEach((button, index) => assert.equal(button.attrs['aria-pressed'], String(index === i)));
  assert.ok(session.nodes['demo-explanation'].textContent.length > 20);
 }
 session.steps[1].events.click();
 assert.match(session.nodes['demo-explanation'].textContent, lang === 'en' ? /old run/ : /旧运行/);
 await session.nodes['copy-command'].events.click();
 assert.equal(session.clipboard.copied, session.nodes.command.textContent);
 assert.match(session.nodes['copy-status'].textContent, lang === 'en' ? /Copied/ : /已复制/);
 session.clipboard.writeText = async () => { throw Error('denied'); };
 await session.nodes['copy-command'].events.click();
 assert.match(session.nodes['copy-status'].textContent, lang === 'en' ? /Select and copy/ : /选中并复制/);
 session.location.hash = '#demo'; session.switcher.events.click();
 assert.equal(new URL(session.switcher.href).hash, '#demo');
}
assert.equal(new URL(start({ browser: 'zh-CN', url: 'https://example.test/phoenix/#demo' }).location.redirect).pathname, '/phoenix/zh.html');
assert.equal(new URL(start({ remembered: 'zh' }).location.redirect).searchParams.get('lang'), 'zh');
const englishOverride = start({ remembered: 'zh', browser: 'zh-CN', url: 'https://example.test/phoenix/?lang=en' });
assert.equal(englishOverride.location.redirect, undefined); assert.equal(englishOverride.storage.value, 'en');
assert.equal(start({ lang: 'zh-CN', url: 'https://example.test/phoenix/zh.html', remembered: 'en' }).location.redirect, undefined);
assert.equal(start({ blocked: true, browser: 'en-US', url: 'https://example.test/phoenix/?lang=en' }).location.redirect, undefined);
assert.equal(start({ remembered: 'unexpected', url: 'https://example.test/phoenix/?lang=unexpected' }).location.redirect, undefined);
assert.equal(new URL(start({ lang: 'zh-CN', url: 'https://example.test/phoenix/zh.html?lang=en#demo' }).location.redirect).pathname, '/phoenix/index.html');
for (const page of ['guide.html', 'guide-zh.html']) {
 const html = readFileSync(path.join(root, page), 'utf8');
 const targets = {};
 for (const [, id, text] of html.matchAll(/<(?:code|pre) id="([^"]+)">([\s\S]*?)<\/(?:code|pre)>/g)) targets[id] = { textContent: text };
 const copyButtons = [...html.matchAll(/data-copy="([^"]+)"/g)].map(([, id]) => ({ ...element(), dataset: { copy: id } }));
 const notice = { textContent: '' };
 const messages = { copySuccess: html.match(/data-copy-success="([^"]+)"/)[1], copyFailure: html.match(/data-copy-failure="([^"]+)"/)[1] };
 const clipboard = { async writeText(text) { this.copied = text; } };
 vm.runInNewContext(readFileSync(path.join(root, 'guide.js'), 'utf8'), { navigator: { clipboard }, setTimeout: () => 1, clearTimeout() {}, document: { body: { dataset: messages }, querySelectorAll: () => copyButtons, getElementById: id => id === 'guide-copy-status' ? notice : targets[id] } });
 for (const button of copyButtons) {
  assert.ok(targets[button.dataset.copy], `${page}: missing copy target`);
  await button.events.click(); assert.equal(clipboard.copied, targets[button.dataset.copy].textContent); assert.equal(notice.textContent, messages.copySuccess);
 }
 clipboard.writeText = async () => { throw Error('denied'); };
 await copyButtons[0].events.click(); assert.equal(notice.textContent, messages.copyFailure);
}
const downloadName = 'phoenix-continuity-gate-v0.2.2-preview.zip';
const checksumEntry = readFileSync(path.join(root, 'downloads', 'SHA256SUMS.txt'), 'utf8').trim().match(/^([a-f0-9]{64})\s+(.+)$/);
assert.ok(checksumEntry, 'Malformed published download checksum');
assert.equal(checksumEntry[2], downloadName, 'Checksum points to an unexpected filename');
const actualChecksum = createHash('sha256').update(readFileSync(path.join(root, 'downloads', downloadName))).digest('hex');
assert.equal(actualChecksum, checksumEntry[1], 'Download archive differs from the published checksum');
console.log('PASS: four pages, local resources and cross-page anchors; demo and language selection; command and feedback copying in both languages, including clipboard denial; release download checksum. Browser rendering remains unverified.');
