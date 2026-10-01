const { test, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
require.extensions['.ts'] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, filename);
const { applyEvent, applyRest, emptyChat, mergeHistory, validateFile } = require('../src/features/chat/state.ts');
const { createChatServices } = require('../src/lib/chat-services.ts');
const { createServices } = require('../src/lib/services.ts');
const { connectChat } = require('../src/features/chat/realtime.ts');
const { GET } = require('../src/app/api/attachments/[id]/download/route.ts');
const originalFetch = global.fetch;
const originalSocket = global.WebSocket;
const originalBase = process.env.NEXT_PUBLIC_API_BASE_URL;
afterEach(() => { global.fetch = originalFetch; global.WebSocket = originalSocket; if (originalBase === undefined) delete process.env.NEXT_PUBLIC_API_BASE_URL; else process.env.NEXT_PUBLIC_API_BASE_URL = originalBase; });
const message = { id: 'a', channel_id: 'channel', sender: { id: 'user', full_name: 'User' }, content: 'hello', created_at: '2026-09-29T00:00:00Z', edited_at: null, attachments: [], reactions: [] };
const event = (type, data) => ({ type, data });
const json = data => Response.json({ data });
const bridge = { getToken: () => 'test-token', refresh: async () => 'replacement', clear: () => {} };

test('REST and WebSocket in either order dedupe by id', () => {
  for (const first of ['rest', 'socket']) {
    let state = first === 'rest' ? applyRest(emptyChat, message) : applyEvent(emptyChat, event('message.created', message));
    state = first === 'rest' ? applyEvent(state, event('message.created', message)) : applyRest(state, message);
    assert.deepEqual(state.messages, [message]);
  }
});
test('edits survive stale create/REST and deletes cannot resurrect from history or REST', () => {
  const updated = { ...message, content: 'edited', edited_at: '2026-09-29T01:00:00Z' };
  let state = applyEvent(emptyChat, event('message.updated', updated));
  state = applyRest(state, message);
  assert.equal(state.messages[0].content, 'edited');
  state = applyEvent(state, event('message.deleted', { message_id: message.id }));
  assert.equal(applyRest(mergeHistory(state, [message]), message).messages.length, 0);
});
test('reaction snapshots replace counts; late send response does not wipe reactions', () => {
  let state = applyRest(emptyChat, message);
  const reaction = event('reaction.updated', { message_id: 'a', reactions: [{ emoji: 'like', count: 2 }] });
  state = applyEvent(applyEvent(state, reaction), reaction);
  assert.deepEqual(applyRest(state, message).messages[0].reactions, reaction.data.reactions);
});
test('history merges without replacing newer messages and sorts chronologically', () => {
  const older = { ...message, id: 'b', created_at: '2026-09-28T00:00:00Z' };
  const state = mergeHistory(applyRest(emptyChat, { ...message, content: 'new' }), [message, older]);
  assert.deepEqual(state.messages.map(m => m.id), ['b', 'a']);
  assert.equal(state.messages[1].content, 'new');
});
test('file UX checks exact 25 MB, oversized, empty and unsupported extension', () => {
  assert.equal(validateFile({ name: 'a.PDF', size: 25 * 1024 * 1024 }), '');
  for (const file of [{ name: 'a.txt', size: 25 * 1024 * 1024 + 1 }, { name: 'a.txt', size: 0 }, { name: 'a.exe', size: 1 }]) assert.ok(validateFile(file));
});
test('multipart uses browser boundary, bearer auth and attachment-only contract', async () => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  global.fetch = async (url, options) => {
    assert.equal(url, 'http://backend.example/api/v1/channels/channel/messages/attachments');
    assert.equal(options.headers.Authorization, 'Bearer test-token');
    assert.equal(options.headers['Content-Type'], undefined);
    assert.ok(options.body instanceof FormData);
    assert.equal(options.body.has('content'), false);
    assert.equal(options.body.get('file').name, 'a.txt');
    return json(message);
  };
  assert.deepEqual(await createChatServices(bridge).upload('channel', new File(['hello'], 'a.txt'), ''), message);
});
test('existing JSON auth flow and refresh retry remain compatible', async () => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  let calls = 0; let refreshed = 0;
  global.fetch = async (_url, options) => {
    calls++;
    assert.equal(options.headers['Content-Type'], 'application/json');
    assert.deepEqual(JSON.parse(options.body), { full_name: 'New name' });
    if (calls === 1) return Response.json({ error: { code: 'ACCESS_TOKEN_EXPIRED', message: 'Expired', fields: null } }, { status: 401 });
    assert.equal(options.headers.Authorization, 'Bearer replacement');
    return json({ full_name: 'New name' });
  };
  const api = createServices({ ...bridge, refresh: async () => { refreshed++; return 'replacement'; } });
  assert.equal((await api.update({ full_name: 'New name' })).full_name, 'New name');
  assert.equal(refreshed, 1);
});
test('reaction endpoints encode emoji and use PUT / DELETE', async () => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  const methods = [];
  global.fetch = async (url, options) => { assert.ok(url.endsWith('/reactions/%F0%9F%91%8D')); methods.push(options.method); return options.method === 'DELETE' ? new Response(null, { status: 204 }) : json([]); };
  const api = createChatServices(bridge); await api.react('a', '👍'); await api.unreact('a', '👍'); assert.deepEqual(methods, ['PUT', 'DELETE']);
});
test('WebSocket authenticates in first frame, dispatches events, cleans up on unmount', () => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'https://backend.example';
  const sockets = [];
  global.WebSocket = class { constructor(url) { this.url = String(url); sockets.push(this); } send(text) { this.frame = JSON.parse(text); } close() { this.closed = true; } };
  const events = []; let syncs = 0;
  const dispose = connectChat('channel', bridge, e => events.push(e), () => {}, () => syncs++);
  const socket = sockets[0]; socket.onopen();
  assert.equal(socket.url, 'wss://backend.example/api/v1/ws/channels/channel');
  assert.deepEqual(socket.frame, { type: 'auth', access_token: 'test-token' });
  socket.onmessage({ data: JSON.stringify(event('message.created', message)) });
  assert.equal(events.length, 1); assert.equal(syncs, 1);
  dispose(); assert.ok(socket.closed); assert.equal(socket.onclose, null);
  socket.onmessage({ data: JSON.stringify(event('message.created', message)) }); assert.equal(events.length, 1);
});
test('download relay authorizes with backend and sends no bearer to storage', async () => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  const id = '00000000-0000-0000-0000-000000000001';
  let calls = 0;
  global.fetch = async (url, options) => {
    if (++calls === 1) { assert.equal(url, `http://backend.example/api/v1/attachments/${id}/download`); assert.equal(options.headers.Authorization, 'Bearer test-token'); assert.equal(options.redirect, 'manual'); return new Response(null, { status: 307, headers: { location: 'http://storage.example/signed' } }); }
    assert.equal(url, 'http://storage.example/signed'); assert.equal(options.headers, undefined); return new Response('private content');
  };
  const response = await GET(new Request('http://frontend/api/download', { headers: { authorization: 'Bearer test-token' } }), { params: Promise.resolve({ id }) });
  assert.equal(await response.text(), 'private content'); assert.equal(response.headers.get('cache-control'), 'no-store');
});
test('download relay never fetches storage for anonymous or forbidden requests', async () => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  let calls = 0;
  global.fetch = async () => { calls++; return Response.json({ error: { code: 'ATTACHMENT_ACCESS_DENIED' } }, { status: 403 }); };
  const params = { params: Promise.resolve({ id: '00000000-0000-0000-0000-000000000001' }) };
  assert.equal((await GET(new Request('http://frontend'), params)).status, 401); assert.equal(calls, 0);
  assert.equal((await GET(new Request('http://frontend', { headers: { authorization: 'Bearer token' } }), params)).status, 403); assert.equal(calls, 1);
});
test('WebSocket retries disconnection and cancels pending reconnect on cleanup', async t => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  const sockets = []; const timers = [];
  t.mock.method(global, 'setTimeout', callback => { const timer = { callback }; timers.push(timer); return timer; });
  t.mock.method(global, 'clearTimeout', timer => { if (timer) timer.canceled = true; });
  global.WebSocket = class { constructor() { sockets.push(this); } send() {} close() {} };
  const dispose = connectChat('channel', bridge, () => {}, () => {}, () => {});
  await sockets[0].onclose({ code: 1006 }); assert.equal(timers.length, 1);
  timers[0].callback(); assert.equal(sockets.length, 2);
  await sockets[1].onclose({ code: 1006 }); dispose();
  assert.ok(timers[1].canceled); timers[1].callback(); assert.equal(sockets.length, 2);
});
test('forbidden WebSocket stops, and disposing during auth refresh cannot reconnect', async t => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  const sockets = []; let scheduled = 0;
  t.mock.method(global, 'setTimeout', () => { scheduled++; });
  global.WebSocket = class { constructor() { sockets.push(this); } send() {} close() {} };
  let finish;
  const auth = { ...bridge, refresh: () => new Promise(resolve => { finish = resolve; }) };
  const dispose = connectChat('channel', auth, () => {}, () => {}, () => {});
  await sockets[0].onclose({ code: 4403 }); assert.equal(scheduled, 0);
  const pending = sockets[0].onclose({ code: 4401 }); dispose(); finish('replacement'); await pending;
  assert.equal(scheduled, 0);
});
test('download API uses same-origin authorized relay and returns a blob', async () => {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  global.fetch = async (url, options) => {
    assert.equal(url, '/api/attachments/id/download'); assert.equal(options.headers.Authorization, 'Bearer test-token');
    return new Response('private content');
  };
  assert.equal(await (await createChatServices(bridge).download('id')).text(), 'private content');
});
