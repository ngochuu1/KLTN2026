// Opt-in real stack verification: no route interception, API mocks or fake sockets.
// Creates only uniquely marked fixtures and cleans those exact fixtures in finally.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const { randomUUID, randomBytes, createHash } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const frontend = process.env.FRONTEND_TEST_URL || 'http://localhost:3000';
const backend = process.env.LIVE_API_URL || 'http://localhost:8000';
const backendDir = path.resolve(__dirname, '../../backend');
const python = process.env.LIVE_PYTHON || path.join(backendDir, '.venv-win/Scripts/python.exe');
const marker = `phase3e-${randomUUID()}`;
const accounts = ['owner', 'member', 'outsider'].map(role => ({ role, email: `${marker}-${role}@example.com`, password: randomBytes(24).toString('base64url'), token: null }));
const emails = accounts.map(a => a.email);
const content = Buffer.from('Phase 3E real browser -> FastAPI -> PostgreSQL -> private MinIO\n');
const sha256 = createHash('sha256').update(content).digest('hex');
let checks = 0;
function pass(name) { checks++; console.log(`PASS ${checks}: ${name}`); }
async function api(actor, method, route, body, status = 200, code) {
  const response = await fetch(`${backend}/api/v1${route}`, { method, headers: { ...(actor?.token ? { Authorization: `Bearer ${actor.token}` } : {}), ...(body ? { 'Content-Type': 'application/json' } : {}) }, body: body ? JSON.stringify(body) : undefined, redirect: 'manual' });
  assert.equal(response.status, status, `API ${method}: expected ${status}, got ${response.status}`);
  if (status === 204) return;
  if (status === 307) return response;
  const json = await response.json();
  if (code) assert.equal(json.error.code, code);
  return json.data;
}
function inspect(data) {
  const result = spawnSync(python, ['-m', 'scripts.verify_chat_live_state'], { cwd: backendDir, input: JSON.stringify({ marker, emails, ...data }), encoding: 'utf8', timeout: 30000 });
  assert.equal(result.status, 0, `Scoped DB/storage ${data.action} failed: ${result.stdout || result.error?.name || 'no result'}`);
  console.log(result.stdout.trim());
}
async function login(browser, account) {
  const context = await browser.newContext(); const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const errors = []; const frames = []; const sockets = []; const closed = [];
  page.on('pageerror', error => errors.push(error.message));
  // Observe actual network sockets, without replacing the browser implementation.
  page.on('websocket', socket => {
    sockets.push(socket);
    socket.on('framereceived', ({ payload }) => {
      const frame = JSON.parse(payload.toString()); frames.push({ channel: socket.url().split('/').at(-1), type: frame.type, id: frame.data?.id ?? frame.data?.message_id });
    });
    socket.on('close', () => closed.push(socket));
  });
  await page.goto(`${frontend}/login`);
  await page.getByLabel('Email', { exact: true }).fill(account.email);
  await page.getByLabel('Mật khẩu', { exact: true }).fill(account.password);
  const response = page.waitForResponse(r => r.url().endsWith('/api/v1/auth/login') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  const result = await response; assert.equal(result.status(), 200); account.token = (await result.json()).data.access_token;
  await page.getByRole('heading', { name: `Xin chào, Live ${account.role}` }).waitFor();
  return { context, page, errors, frames, sockets, closed };
}
async function openChannel(session, workspace, name) {
  await session.page.goto(`${frontend}/workspaces/${workspace.id}`);
  await session.page.getByRole('heading', { name: workspace.name, exact: true }).waitFor();
  if (name !== 'general') await session.page.getByRole('button', { name: `# ${name} TEXT`, exact: true }).click();
  await session.page.getByRole('heading', { name: `# ${name}`, exact: true }).waitFor();
  await session.page.getByText('Đã kết nối', { exact: true }).waitFor();
  await session.page.getByRole('button', { name: 'Tải lại tin nhắn', exact: true }).waitFor();
}
async function send(session, text) {
  await session.page.getByLabel(/Nhắn vào #/).fill(text);
  const response = session.page.waitForResponse(r => /\/channels\/[^/]+\/messages$/.test(r.url()) && r.request().method() === 'POST');
  await session.page.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).click();
  const result = await response; assert.equal(result.status(), 201); return (await result.json()).data;
}
async function messageVisible(session, id, text) {
  const item = session.page.locator(`[data-message-id="${id}"]`);
  await item.getByText(text, { exact: true }).waitFor(); assert.equal(await item.count(), 1); return item;
}

(async () => {
  let browser;
  const sessions = [];
  try {
    await api(null, 'GET', '/channels/' + randomUUID() + '/messages', null, 401, 'AUTHENTICATION_REQUIRED');
    for (const account of accounts) {
      const user = await api(null, 'POST', '/auth/register', { full_name: `Live ${account.role}`, email: account.email, password: account.password, confirm_password: account.password }, 201); account.id = user.id;
    }
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    for (const account of accounts) sessions.push(await login(browser, account));
    const [a, b, outside] = sessions; const [owner, member, outsider] = accounts;
    pass('three independent real browser logins and unauthenticated API boundary');
    const workspace = await api(owner, 'POST', '/workspaces', { name: marker }, 201);
    const invite = await api(owner, 'POST', `/workspaces/${workspace.id}/invitations`, { invitee_user_id: member.id }, 201);
    await api(member, 'POST', `/workspace-invitations/${invite.token}/accept`);
    await openChannel(a, workspace, 'general'); await openChannel(b, workspace, 'general');
    const channels = await api(owner, 'GET', `/workspaces/${workspace.id}/channels`); const general = channels.find(c => c.is_default);
    assert.ok(general); assert.equal(await b.page.getByRole('button', { name: 'Tạo Channel', exact: true }).count(), 0);
    assert.equal(await a.page.getByRole('button', { name: 'Xóa Channel', exact: true }).count(), 0);
    await api(owner, 'DELETE', `/channels/${general.id}`, null, 403, 'DEFAULT_CHANNEL_CANNOT_BE_DELETED');
    await api(member, 'POST', `/workspaces/${workspace.id}/channels`, { name: 'denied', type: 'TEXT' }, 403, 'CHANNEL_PERMISSION_DENIED');
    await api(member, 'PATCH', `/channels/${general.id}`, { name: 'denied' }, 403, 'CHANNEL_PERMISSION_DENIED');
    await api(member, 'DELETE', `/channels/${general.id}`, null, 403, 'CHANNEL_PERMISSION_DENIED');
    pass('live channel list/default protection/MEMBER management denial');
    const p = a.page;
    await p.getByRole('button', { name: 'Tạo Channel', exact: true }).click();
    await p.getByLabel('Tên Channel', { exact: true }).fill('general'); await p.getByRole('button', { name: 'Lưu Channel', exact: true }).click();
    await p.getByText('Tên Channel đã tồn tại', { exact: true }).waitFor();
    await p.getByLabel('Tên Channel', { exact: true }).fill('live-channel');
    const createdResponse = p.waitForResponse(r => r.url().endsWith(`/workspaces/${workspace.id}/channels`) && r.request().method() === 'POST' && r.status() === 201);
    await p.getByRole('button', { name: 'Lưu Channel', exact: true }).click(); const created = (await (await createdResponse).json()).data;
    await p.getByRole('heading', { name: '# live-channel', exact: true }).waitFor();
    await p.reload(); await p.getByRole('button', { name: '# live-channel TEXT', exact: true }).click();
    await p.getByRole('button', { name: 'Sửa Channel', exact: true }).click(); await p.getByLabel('Tên Channel', { exact: true }).fill('live-renamed');
    await p.getByRole('button', { name: 'Lưu Channel', exact: true }).click(); await p.getByRole('heading', { name: '# live-renamed', exact: true }).waitFor();
    await openChannel(b, workspace, 'live-renamed');
    pass('Channel create/duplicate/reload/update through real frontend and API');
    await api(owner, 'POST', `/workspaces/${workspace.id}/channels`, { name: 'live-study', type: 'STUDY_ROOM' }, 201);
    const disposable = await api(owner, 'POST', `/workspaces/${workspace.id}/channels`, { name: 'live-delete', type: 'TEXT' }, 201);
    await p.reload(); await p.getByRole('button', { name: '◇ live-study STUDY_ROOM', exact: true }).click();
    await p.getByText('Chưa có thành viên trong phòng.', { exact: true }).waitFor();
    assert.equal(await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).count(), 0);
    await p.getByRole('button', { name: '# live-delete TEXT', exact: true }).click();
    p.on('dialog', dialog => dialog.accept());
    await p.getByRole('button', { name: 'Xóa Channel', exact: true }).click();
    await p.getByRole('button', { name: '# live-delete TEXT', exact: true }).waitFor({ state: 'detached' });
    await api(owner, 'GET', `/channels/${disposable.id}`, null, 404, 'CHANNEL_NOT_FOUND');
    await p.getByRole('button', { name: '# live-renamed TEXT', exact: true }).click();
    pass('channel switching/STUDY_ROOM empty state/deletion with actual API 404');
    assert.ok(await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).isDisabled());
    await p.getByLabel(/Nhắn vào #/).fill('   '); assert.ok(await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).isDisabled());
    await api(owner, 'POST', `/channels/${created.id}/messages`, { content: '   ' }, 422, 'INVALID_MESSAGE_CONTENT');
    const sent = await send(a, 'Live persistent'); await messageVisible(b, sent.id, 'Live persistent'); await messageVisible(a, sent.id, 'Live persistent');
    assert.ok(b.frames.some(f => f.id === sent.id && f.type === 'message.created'));
    pass('A sends, B receives actual message.created without reload; dedupe/empty composer');
    let own = p.locator(`[data-message-id="${sent.id}"]`);
    assert.equal(await b.page.locator(`[data-message-id="${sent.id}"]`).getByRole('button', { name: 'Sửa tin nhắn', exact: true }).count(), 0);
    await own.getByRole('button', { name: 'Sửa tin nhắn', exact: true }).click(); await own.getByLabel('Sửa tin nhắn', { exact: true }).fill('Live edited persistent');
    await own.getByRole('button', { name: 'Lưu tin nhắn', exact: true }).click(); await messageVisible(b, sent.id, 'Live edited persistent');
    await b.page.locator(`[data-message-id="${sent.id}"]`).getByText('Đã chỉnh sửa', { exact: true }).waitFor();
    assert.ok(b.frames.some(f => f.id === sent.id && f.type === 'message.updated'));
    pass('own edit and remote edited state over real message.updated');
    await own.locator('summary').click(); await own.getByRole('button', { name: 'Thêm 👍', exact: true }).click();
    const remote = b.page.locator(`[data-message-id="${sent.id}"]`);
    await remote.locator('.reactions').getByText('👍 1', { exact: true }).waitFor();
    await remote.locator('summary').click(); await remote.getByRole('button', { name: 'Thêm 👍', exact: true }).click();
    await own.locator('.reactions').getByText('👍 2', { exact: true }).waitFor();
    await remote.getByRole('button', { name: 'Thêm 👍', exact: true }).click();
    await remote.getByRole('button', { name: 'Gỡ 👍 của tôi', exact: true }).click();
    await own.locator('.reactions').getByText('👍 1', { exact: true }).waitFor();
    assert.ok(a.frames.some(f => f.id === sent.id && f.type === 'reaction.updated'));
    pass('two-user real reaction add/idempotence/remove with correct aggregate');
    const removed = await send(a, 'Live delete me'); await messageVisible(b, removed.id, 'Live delete me');
    await p.locator(`[data-message-id="${removed.id}"]`).getByRole('button', { name: 'Xóa tin nhắn', exact: true }).click();
    await b.page.locator(`[data-message-id="${removed.id}"]`).waitFor({ state: 'detached' });
    assert.ok(b.frames.some(f => f.id === removed.id && f.type === 'message.deleted'));
    pass('live delete propagates to the second user without reload');
    for (const file of [{ name: 'bad.exe', mimeType: 'application/octet-stream', buffer: Buffer.from('x') }, { name: 'empty.txt', mimeType: 'text/plain', buffer: Buffer.alloc(0) }, { name: 'large.txt', mimeType: 'text/plain', buffer: Buffer.alloc(25 * 1024 * 1024 + 1) }]) {
      await p.getByLabel('Đính kèm tệp (tối đa 25 MB)').setInputFiles(file);
      assert.ok(await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).isDisabled());
      assert.ok(await p.locator('.message-composer [role="alert"]').isVisible());
    }
    await p.getByLabel('Đính kèm tệp (tối đa 25 MB)').setInputFiles({ name: 'phase3e-live.txt', mimeType: 'text/plain', buffer: content });
    const uploadedResponse = p.waitForResponse(r => r.url().endsWith(`/channels/${created.id}/messages/attachments`) && r.request().method() === 'POST');
    await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).click();
    const uploadResponse = await uploadedResponse; assert.equal(uploadResponse.status(), 201); const uploaded = (await uploadResponse.json()).data; const attachment = uploaded.attachments[0];
    assert.equal(uploaded.content, null); assert.deepEqual(Object.keys(attachment).sort(), ['content_type', 'id', 'original_filename', 'size_bytes']);
    const downloadButton = b.page.getByRole('button', { name: 'Tải phase3e-live.txt (1 KB)', exact: true }); await downloadButton.waitFor();
    const downloadEvent = b.page.waitForEvent('download'); await downloadButton.click(); const download = await downloadEvent;
    const stream = await download.createReadStream(); const bytes = []; for await (const chunk of stream) bytes.push(chunk);
    assert.equal(createHash('sha256').update(Buffer.concat(bytes)).digest('hex'), sha256);
    const signed = await api(member, 'GET', `/attachments/${attachment.id}/download`, null, 307);
    const object = await fetch(signed.headers.get('location')); assert.equal(object.status, 200);
    assert.equal(createHash('sha256').update(Buffer.from(await object.arrayBuffer())).digest('hex'), sha256);
    pass('real browser attachment-only upload, second-user download and presigned content integrity');
    await openChannel(a, workspace, 'live-renamed'); await openChannel(b, workspace, 'live-renamed');
    own = await messageVisible(a, sent.id, 'Live edited persistent');
    await own.getByText('Đã chỉnh sửa', { exact: true }).waitFor(); await own.locator('.reactions').getByText('👍 1', { exact: true }).waitFor();
    await b.page.getByRole('button', { name: 'Tải phase3e-live.txt (1 KB)', exact: true }).waitFor();
    assert.equal(await b.page.locator(`[data-message-id="${removed.id}"]`).count(), 0);
    pass('full page reload restores channels/messages/edit/reaction/attachment from PostgreSQL');
    await api(member, 'PATCH', `/messages/${sent.id}`, { content: 'denied' }, 403, 'MESSAGE_PERMISSION_DENIED');
    await api(member, 'DELETE', `/messages/${sent.id}`, null, 403, 'MESSAGE_PERMISSION_DENIED');
    await api(outsider, 'GET', `/channels/${created.id}/messages`, null, 403, 'CHANNEL_ACCESS_DENIED');
    await api(outsider, 'GET', `/attachments/${attachment.id}/download`, null, 403, 'ATTACHMENT_ACCESS_DENIED');
    await api(null, 'GET', `/attachments/${attachment.id}/download`, null, 401, 'AUTHENTICATION_REQUIRED');
    await api(owner, 'GET', `/channels/${randomUUID()}/messages`, null, 404, 'CHANNEL_NOT_FOUND');
    await api(owner, 'PATCH', `/messages/${randomUUID()}`, { content: 'missing' }, 404, 'MESSAGE_NOT_FOUND');
    await outside.page.goto(`${frontend}/workspaces/${workspace.id}`); await outside.page.locator('[role="alert"]').waitFor();
    assert.equal(await outside.page.locator('.message-list').count(), 0);
    const code = await outside.page.evaluate(({ backend, channel, token }) => new Promise(resolve => {
      const socket = new WebSocket(`${backend.replace('http', 'ws')}/api/v1/ws/channels/${channel}`);
      socket.onopen = () => socket.send(JSON.stringify({ type: 'auth', access_token: token }));
      socket.onclose = event => resolve(event.code);
    }), { backend, channel: created.id, token: outsider.token });
    assert.equal(code, 4403);
    const invalidCode = await outside.page.evaluate(({ backend, channel }) => new Promise(resolve => {
      const socket = new WebSocket(`${backend.replace('http', 'ws')}/api/v1/ws/channels/${channel}`);
      socket.onopen = () => socket.send(JSON.stringify({ type: 'auth', access_token: 'invalid' }));
      socket.onclose = event => resolve(event.code);
    }), { backend, channel: created.id });
    assert.equal(invalidCode, 4401);
    const downloadDenial = await outside.page.evaluate(async ({ id, token }) => {
      const anonymous = await fetch(`/api/attachments/${id}/download`);
      const forbidden = await fetch(`/api/attachments/${id}/download`, { headers: { Authorization: `Bearer ${token}` } });
      return [anonymous.status, forbidden.status, forbidden.headers.get('location')];
    }, { id: attachment.id, token: outsider.token });
    assert.deepEqual(downloadDenial, [401, 403, null]);
    pass('real non-member REST/UI/WebSocket and unauthorized message/download boundaries');
    const priorClosed = b.closed.length;
    await b.page.getByRole('button', { name: '# general TEXT', exact: true }).click();
    await b.page.getByRole('heading', { name: '# general', exact: true }).waitFor();
    assert.ok(b.closed.length > priorClosed);
    await b.page.getByRole('button', { name: '# live-renamed TEXT', exact: true }).click(); await b.page.getByText('Đã kết nối', { exact: true }).waitFor();
    pass('real socket cleanup and new subscription when switching channel');
    // Close the actual native socket using DevTools heap inspection. No WebSocket
    // replacement/interception: production reconnect logic must open a new one.
    const cdp = await b.context.newCDPSession(b.page);
    const prototype = await cdp.send('Runtime.evaluate', { expression: 'WebSocket.prototype', objectGroup: 'phase3e-reconnect' });
    const objects = await cdp.send('Runtime.queryObjects', { prototypeObjectId: prototype.result.objectId, objectGroup: 'phase3e-reconnect' });
    const socketCount = b.sockets.length;
    const disconnected = await cdp.send('Runtime.callFunctionOn', {
      objectId: objects.objects.objectId,
      functionDeclaration: 'function(channel) { const socket = this.find(s => s.readyState === WebSocket.OPEN && s.url.endsWith(channel)); if (!socket) return false; socket.close(4000, "live reconnect verification"); return true; }',
      arguments: [{ value: created.id }], returnByValue: true,
    });
    assert.equal(disconnected.result.value, true);
    const missed = await api(owner, 'POST', `/channels/${created.id}/messages`, { content: 'Sent during reconnect' }, 201);
    await messageVisible(b, missed.id, 'Sent during reconnect');
    assert.ok(b.sockets.length > socketCount);
    const afterReconnect = await send(a, 'Realtime after reconnect'); await messageVisible(b, afterReconnect.id, 'Realtime after reconnect');
    assert.ok(b.frames.some(f => f.id === afterReconnect.id && f.type === 'message.created'));
    await cdp.send('Runtime.releaseObjectGroup', { objectGroup: 'phase3e-reconnect' }); await cdp.detach();
    pass('actual socket disconnect/reconnect, missed-history recovery and resumed remote events');
    inspect({ action: 'inspect', workspace_id: workspace.id, deleted_channel_id: disposable.id, edited_message_id: sent.id, deleted_message_id: removed.id, attachment_id: attachment.id, sha256 });
    pass('direct PostgreSQL rows, physical private MinIO object, hash and anonymous AccessDenied');
    for (const session of sessions) assert.deepEqual(session.errors, []);
    console.log(`LIVE PASS: ${checks} scenarios; no mocked API or WebSocket`);
  } finally {
    if (browser) await browser.close();
    inspect({ action: 'cleanup' });
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
