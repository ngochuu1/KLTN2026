// Browser contract verification against the production frontend. No backend data
// is mutated. Supply PLAYWRIGHT_MODULE if Playwright is installed outside the repo.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const base = process.env.FRONTEND_TEST_URL || 'http://localhost:3100';
const uid = '00000000-0000-0000-0000-000000000001';
const cid = '00000000-0000-0000-0000-000000000002';
const second = '00000000-0000-0000-0000-000000000003';
const study = '00000000-0000-0000-0000-000000000004';
const date = '2026-09-29T00:00:00Z';
const user = { id: uid, full_name: 'Test Owner', email: 'test@example.com', status: 'ACTIVE', system_role: 'USER' };
const channel = (id, name, type = 'TEXT') => ({ id, name, type, workspace_id: 'workspace', is_default: id === cid, description: null, created_at: date, updated_at: date });
const initial = { id: 'message1', channel_id: cid, content: 'History message', sender: user, created_at: date, edited_at: null, attachments: [], reactions: [] };
async function fixture(browser, role = 'OWNER', fail = false) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error' && message.text().includes('Encountered two children with the same key')) errors.push(message.text());
  });
  const sockets = []; const closed = [];
  let channels = [channel(cid, 'general'), channel(second, 'other'), channel(study, 'study', 'STUDY_ROOM')];
  let messages = [structuredClone(initial), { ...structuredClone(initial), id: 'message2', content: '<script>unsafe()</script>', sender: { id: 'other-user', full_name: 'Other Member' } }];
  let serial = 0; let downloaded = false; let deny = false; let denyRoom = false;
  let denyMedia = false;
  const mediaWaiters = [];
  await page.addInitScript(() => {
    window.mediaCaptureCalls = 0;
    navigator.mediaDevices.getUserMedia = async () => { window.mediaCaptureCalls++; throw new DOMException('Test denies media capture', 'NotAllowedError'); };
  });
  const emit = event => { for (const socket of sockets.filter(s => !closed.includes(s) && s.url().endsWith(cid))) socket.send(JSON.stringify(event)); };
  await page.routeWebSocket('**/api/v1/ws/channels/**', socket => {
    sockets.push(socket);
    socket.onMessage(text => { const frame = JSON.parse(text); assert.deepEqual(frame, { type: 'auth', access_token: 'browser-fixture-token' }); });
    socket.onClose(() => { if (!closed.includes(socket)) closed.push(socket); });
  });
  await page.routeWebSocket('**/api/v1/ws/study-rooms/**', socket => {
    sockets.push(socket);
    let joined = false;
    let devices = { microphone_enabled: false, camera_enabled: false };
    socket.onMessage(text => {
      const frame = JSON.parse(text);
      if (denyRoom) { socket.close({ code: 4403 }); return; }
      if (frame.type === 'join' && !joined) { joined = true; devices = { microphone_enabled: false, camera_enabled: false }; }
      if (frame.type === 'leave') { joined = false; devices = { microphone_enabled: false, camera_enabled: false }; mediaWaiters.splice(0).forEach(resolve => resolve()); }
      if (frame.type === 'devices') { assert.ok(joined); const { type, ...fields } = frame; assert.equal(type, 'devices'); devices = { ...devices, ...fields }; }
      socket.send(JSON.stringify({ type: 'room.state', data: { channel: channel(study, 'study', 'STUDY_ROOM'), self_state: joined ? 'IN_ROOM' : 'LEFT', self_devices: devices, participants: joined ? [{ user_id: uid, full_name: user.full_name, state: 'IN_ROOM', joined_at: date, ...devices }] : [] } }));
    });
    socket.onClose(() => { if (!closed.includes(socket)) closed.push(socket); });
  });
  await page.route('**/api/attachments/*/download', async route => {
    assert.equal(route.request().headers().authorization, 'Bearer browser-fixture-token'); downloaded = true;
    await route.fulfill({ contentType: 'application/octet-stream', body: 'hello attachment' });
  });
  await page.route('**/api/v1/**', async route => {
    const request = route.request(); const url = new URL(request.url()); const path = url.pathname.replace('/api/v1', ''); const method = request.method();
    const ok = data => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ data }) });
    const failure = (status, code, message) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify({ error: { code, message, fields: null } }) });
    if (path === '/auth/refresh') return ok({ access_token: 'browser-fixture-token' });
    if (path === '/users/me') return ok(user);
    if (path === '/workspaces/workspace') return ok({ id: 'workspace', name: 'Frontend verification', role, description: null, created_at: date, updated_at: date });
    if (path === '/workspaces/workspace/members') return ok([{ user_id: uid, full_name: user.full_name, email: user.email, role, joined_at: date }]);
    if (path === '/workspaces') return ok([]);
    if (path.endsWith('/study-room/media-token')) {
      // Hold credential response while checking leave/switch cancellation. This is
      // not a simulated successful LiveKit connection or live media verification.
      if (!denyMedia) await new Promise(resolve => mediaWaiters.push(resolve));
      return failure(503, 'MEDIA_NOT_CONFIGURED', 'Media service unavailable');
    }
    if (path === '/workspaces/workspace/channels') {
      if (fail) return failure(403, 'CHANNEL_PERMISSION_DENIED', 'Không có quyền truy cập Channel');
      if (method === 'GET') return ok(channels);
      const body = request.postDataJSON();
      if (channels.some(c => c.name === body.name)) return failure(409, 'CHANNEL_NAME_ALREADY_EXISTS', 'Tên Channel đã tồn tại');
      const created = { ...channel(`new-${++serial}`, body.name, body.type), description: body.description }; channels.push(created); return ok(created);
    }
    if (/^\/channels\/[^/]+$/.test(path)) {
      const id = path.split('/')[2];
      if (method === 'PATCH') { channels = channels.map(c => c.id === id ? { ...c, ...request.postDataJSON() } : c); return ok(channels.find(c => c.id === id)); }
      channels = channels.filter(c => c.id !== id); return route.fulfill({ status: 204 });
    }
    if (path.includes('/messages') && path.startsWith('/channels/')) {
      const id = path.split('/')[2];
      if (method === 'GET') return ok(messages.filter(m => m.channel_id === id).slice().reverse());
      if (deny) return failure(403, 'CHANNEL_ACCESS_DENIED', 'Bạn không có quyền gửi tin nhắn');
      const upload = path.endsWith('/attachments');
      if (upload) assert.ok(request.headers()['content-type'].startsWith('multipart/form-data; boundary='));
      const msg = { ...structuredClone(initial), id: `sent-${++serial}`, channel_id: id, content: upload ? null : request.postDataJSON().content, created_at: '2026-09-29T01:00:00Z', attachments: upload ? [{ id: 'attachment1', original_filename: 'note.txt', content_type: 'text/plain', size_bytes: 16 }] : [] };
      messages.push(msg); emit({ type: 'message.created', data: msg }); await ok(msg); return;
    }
    if (path.includes('/reactions/')) {
      const id = path.split('/')[2]; const emoji = decodeURIComponent(path.split('/')[4]);
      const msg = messages.find(m => m.id === id); msg.reactions = method === 'PUT' ? [{ emoji, count: 1 }] : [];
      emit({ type: 'reaction.updated', data: { message_id: id, reactions: msg.reactions } });
      return method === 'PUT' ? ok(msg.reactions) : route.fulfill({ status: 204 });
    }
    if (path.startsWith('/messages/')) {
      const id = path.split('/')[2];
      if (method === 'PATCH') { const msg = messages.find(m => m.id === id); msg.content = request.postDataJSON().content; msg.edited_at = '2026-09-29T02:00:00Z'; emit({ type: 'message.updated', data: msg }); return ok(msg); }
      messages = messages.filter(m => m.id !== id); emit({ type: 'message.deleted', data: { message_id: id } }); return route.fulfill({ status: 204 });
    }
    return failure(404, 'NOT_FOUND', path);
  });
  await page.goto(`${base}/workspaces/workspace`);
  await page.getByRole('heading', { name: 'Frontend verification' }).waitFor().catch(error => { console.error(errors); throw error; });
  return { context, page, errors, sockets, closed, emit, download: () => downloaded, deny: () => { deny = true; }, denyRoom: () => { denyRoom = true; }, denyMedia: () => { denyMedia = true; } };
}

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  let checks = 0;
  try {
    const f = await fixture(browser); const p = f.page;
    await p.getByText('History message', { exact: true }).waitFor();
    assert.equal(await p.locator('[data-message-id="message2"] script').count(), 0);
    assert.equal(await p.locator('[data-message-id="message2"]').getByRole('button', { name: 'Sửa tin nhắn', exact: true }).count(), 0); checks++;
    assert.equal(await p.getByRole('button', { name: 'Xóa Channel', exact: true }).count(), 0);
    await p.getByRole('button', { name: '# other TEXT' }).click();
    await p.getByText('Chưa có tin nhắn.', { exact: false }).waitFor();
    await p.waitForFunction(() => !document.querySelector('[data-message-id="message1"]'));
    await p.getByRole('button', { name: '◇ study STUDY_ROOM' }).click();
    await p.getByText('Chưa có thành viên trong phòng.').waitFor();
    for (const name of ['Microphone: OFF', 'Camera: OFF', 'Chia s? m?n h?nh']) assert.ok(await p.getByRole('button', { name, exact: true }).isDisabled());
    await p.getByRole('button', { name: 'Tham gia phòng', exact: true }).click();
    await p.getByText('Bạn đang ở trong phòng.', { exact: true }).waitFor();
    await p.getByRole('list', { name: 'Thành viên trong phòng', exact: true }).getByText('Test Owner · Đang trong phòng').waitFor();
    await p.getByText('Đang kết nối media…', { exact: true }).waitFor();
    for (const name of ['Microphone: OFF', 'Camera: OFF', 'Chia s? m?n h?nh']) assert.ok(await p.getByRole('button', { name, exact: true }).isDisabled());
    await p.getByRole('button', { name: 'Rời phòng', exact: true }).click();
    await p.getByText('Chưa có thành viên trong phòng.').waitFor();
    checks++;
    for (const name of ['Microphone: OFF', 'Camera: OFF', 'Chia s? m?n h?nh']) assert.ok(await p.getByRole('button', { name, exact: true }).isDisabled());
    f.denyMedia();
    await p.getByRole('button', { name: 'Tham gia phòng', exact: true }).click();
    await p.getByText('Media đã ngắt hoặc không thể kết nối. Hãy tham gia lại phòng.', { exact: true }).waitFor();
    await p.getByText('Bạn đang ở ngoài phòng.', { exact: true }).waitFor();
    assert.equal(await p.evaluate(() => window.mediaCaptureCalls), 0); checks++;
    const roomSocket = f.sockets.find(s => s.url().includes('/ws/study-rooms/'));
    roomSocket.close({ code: 1001 });
    await p.getByText('Đã ngắt kết nối phòng. Vui lòng kết nối lại.', { exact: true }).waitFor();
    await p.getByRole('button', { name: 'Kết nối lại', exact: true }).click();
    await p.getByText('Chưa có thành viên trong phòng.').waitFor(); checks++;
    f.denyRoom();
    await p.getByRole('button', { name: 'Tham gia phòng', exact: true }).click();
    await p.getByText('Không có quyền truy cập hoặc phòng không còn tồn tại.', { exact: true }).waitFor(); checks++;
    assert.equal(await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).count(), 0);
    await p.getByRole('button', { name: '# general TEXT' }).click();
    await p.getByText('History message', { exact: true }).waitFor();
    assert.ok(f.closed.length >= 2); checks++;
    await p.getByLabel('Nhắn vào #general').fill('New message');
    await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).click();
    await p.getByRole('list', { name: 'Tin nhắn' }).getByText('New message', { exact: true }).waitFor();
    assert.equal(await p.getByRole('list', { name: 'Tin nhắn' }).getByText('New message', { exact: true }).count(), 1); checks++;
    const remote = { ...initial, id: 'remote', content: 'Remote message', sender: { id: 'remote-user', full_name: 'Remote Member' } };
    f.emit({ type: 'message.created', data: remote });
    await p.getByText('Remote message', { exact: true }).waitFor();
    f.emit({ type: 'message.updated', data: { ...remote, content: 'Remote edit', edited_at: '2026-09-29T03:00:00Z' } });
    await p.getByText('Remote edit', { exact: true }).waitFor();
    f.emit({ type: 'reaction.updated', data: { message_id: 'remote', reactions: [{ emoji: '🎉', count: 2 }] } });
    await p.locator('[data-message-id="remote"] .reactions').getByText('🎉 2', { exact: true }).waitFor();
    f.emit({ type: 'message.deleted', data: { message_id: 'remote' } });
    await p.locator('[data-message-id="remote"]').waitFor({ state: 'detached' }); checks++;
    const own = p.locator('[data-message-id="message1"]');
    await own.getByRole('button', { name: 'Sửa tin nhắn', exact: true }).click();
    await own.getByLabel('Sửa tin nhắn', { exact: true }).fill('Edited message');
    await own.getByRole('button', { name: 'Lưu tin nhắn' }).click();
    await own.getByText('Edited message', { exact: true }).waitFor();
    await own.getByText('Đã chỉnh sửa', { exact: true }).waitFor(); checks++;
    await own.locator('summary').click();
    await own.getByRole('button', { name: 'Thêm 👍', exact: true }).click();
    await own.locator('.reactions').getByText('👍 1', { exact: true }).waitFor();
    await own.getByRole('button', { name: 'Gỡ 👍 của tôi', exact: true }).click();
    await p.waitForFunction(() => document.querySelector('[data-message-id="message1"] .reactions').textContent === ''); checks++;
    await p.getByLabel('Đính kèm tệp (tối đa 25 MB)').setInputFiles({ name: 'bad.exe', mimeType: 'application/octet-stream', buffer: Buffer.from('x') });
    await p.getByText('Chỉ hỗ trợ PDF, Word, TXT, PNG và JPG.').waitFor();
    assert.ok(await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).isDisabled());
    await p.getByLabel('Đính kèm tệp (tối đa 25 MB)').setInputFiles({ name: 'note.txt', mimeType: 'text/plain', buffer: Buffer.from('hello attachment') });
    await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).click();
    const download = p.waitForEvent('download'); await p.getByRole('button', { name: 'Tải note.txt (1 KB)' }).click();
    assert.equal((await download).suggestedFilename(), 'note.txt'); assert.ok(f.download()); checks++;
    p.on('dialog', dialog => dialog.accept());
    await own.getByRole('button', { name: 'Xóa tin nhắn', exact: true }).click();
    await own.waitFor({ state: 'detached' }); checks++;
    await p.getByRole('button', { name: 'Tạo Channel', exact: true }).click();
    await p.getByLabel('Tên Channel', { exact: true }).fill('general');
    await p.getByRole('button', { name: 'Lưu Channel' }).click();
    await p.getByText('Tên Channel đã tồn tại', { exact: true }).waitFor();
    await p.getByLabel('Tên Channel', { exact: true }).fill('created');
    await p.getByRole('button', { name: 'Lưu Channel' }).click();
    await p.getByRole('heading', { name: '# created', exact: true }).waitFor();
    await p.getByRole('button', { name: 'Sửa Channel', exact: true }).click();
    await p.getByLabel('Tên Channel', { exact: true }).fill('renamed');
    await p.getByRole('button', { name: 'Lưu Channel' }).click();
    await p.getByRole('heading', { name: '# renamed', exact: true }).waitFor();
    await p.getByRole('button', { name: 'Xóa Channel', exact: true }).click();
    await p.getByRole('heading', { name: '# general', exact: true }).waitFor(); checks++;
    f.deny(); await p.getByLabel('Nhắn vào #general').fill('denied'); await p.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).click();
    await p.getByText('Bạn không có quyền gửi tin nhắn', { exact: true }).waitFor();
    assert.equal(await p.getByLabel('Nhắn vào #general').inputValue(), 'denied'); checks++;
    await p.setViewportSize({ width: 390, height: 844 });
    assert.ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); checks++;
    await p.getByRole('link', { name: 'Danh sách Workspace' }).click();
    await p.getByRole('heading', { name: 'Workspace của bạn' }).waitFor();
    assert.equal(f.closed.length, f.sockets.length); assert.deepEqual(f.errors, []); checks++;
    await f.context.close();
    for (const role of ['MEMBER', 'ADMIN']) {
      const f = await fixture(browser, role); await f.page.getByText('History message', { exact: true }).waitFor();
      assert.equal(await f.page.getByRole('button', { name: 'Tạo Channel', exact: true }).count(), role === 'MEMBER' ? 0 : 1);
      assert.equal(await f.page.getByRole('button', { name: 'Sửa Channel', exact: true }).count(), role === 'MEMBER' ? 0 : 1);
      assert.deepEqual(f.errors, []); await f.context.close(); checks++;
    }
    const denied = await fixture(browser, 'MEMBER', true); await denied.page.getByText('Không có quyền truy cập Channel', { exact: true }).waitFor();
    assert.deepEqual(denied.errors, []); await denied.context.close(); checks++;
    console.log(`PASS: ${checks} browser scenarios (mocked API/WebSocket contracts)`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
