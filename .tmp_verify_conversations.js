const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('d:/Doubao/DeepTutor/data/user/integrations/LinkMind/lagi-web/src/main/webapp/js/conversations.js', 'utf8');
const store = {};
const sandbox = {
  console,
  localStorage: { getItem: (k) => Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null, setItem: (k, v) => { store[k] = String(v); } },
  window: { tText: (s) => s, tHtml: (s) => s, addEventListener: () => {} },
  document: { getElementById: () => null },
  marked: { parse: (s) => '<p>' + String(s).trim() + '</p>' },
  echarts: { init: () => ({ setOption() {}, clear() {}, resize() {} }) },
  $: () => ({ data() { return this; }, html() { return this; }, closest() { return this; }, find() { return this; }, children() { return this; }, append() { return this; }, show() { return this; }, hide() { return this; }, prop() { return 0; }, scrollTop() { return this; }, length: 0 })
};
sandbox.global = sandbox;
vm.createContext(sandbox);
vm.runInContext(src, sandbox);
sandbox.setThinkHiddenPreference(true);
console.log('ARRAY_OK', sandbox.renderAssistantContent(['<think>推理</think>', '结果']).includes('结果'));
console.log('NUMBER_OK', sandbox.renderAssistantContent(123) === '<p>123</p>');
console.log('OBJECT_OK', sandbox.renderAssistantContent({a:1}).includes('[object Object]'));
