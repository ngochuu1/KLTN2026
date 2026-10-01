// Real application + LiveKit/WebRTC. Chrome synthetic capture devices supply
// media; no API, signaling, SDK, RTCPeerConnection or track mocks.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const { randomUUID, randomBytes } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const frontend = process.env.FRONTEND_TEST_URL || 'http://localhost:3000';
const backend = process.env.LIVE_API_URL || 'http://localhost:8000';
const screenTest = process.argv.includes('--screen-share');
const marker = `phase4c-${randomUUID()}`;
const accounts = ['owner', 'member'].map(role => ({ role, email: `${marker}-${role}@example.com`, password: randomBytes(24).toString('base64url') }));
async function api(actor, method, route, body, status = 200) {
  const response = await fetch(`${backend}/api/v1${route}`, { method, headers: { ...(actor?.token ? { Authorization: `Bearer ${actor.token}` } : {}), ...(body ? { 'Content-Type': 'application/json' } : {}) }, body: body ? JSON.stringify(body) : undefined });
  assert.equal(response.status, status, `${method} ${route}: ${response.status}`);
  return status === 204 ? null : (await response.json()).data;
}
(async () => {
  let browser; const contexts = []; const errors = [];
  try {
    for (const account of accounts) {
      const user = await api(null, 'POST', '/auth/register', { full_name: `Media ${account.role}`, email: account.email, password: account.password, confirm_password: account.password }, 201);
      account.id = user.id;
    }
    browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-fake-device-for-media-stream', '--auto-accept-camera-and-microphone-capture', '--autoplay-policy=no-user-gesture-required', ...(screenTest ? ['--auto-select-tab-capture-source-by-title=UC26 screen fixture'] : [])] });
    let source;
    const openSource = async () => {
      const context = await browser.newContext(); contexts.push(context);
      source = await context.newPage();
      await source.goto('data:text/html,<title>UC26 screen fixture</title><body style="margin:0;background:rgb(20,180,80)"><h1>UC26 real tab capture</h1></body>');
    };
    if (screenTest) await openSource();
    const pages = [];
    for (const account of accounts) {
      const context = await browser.newContext({ permissions: ['camera', 'microphone'] }); contexts.push(context);
      const page = await context.newPage(); page.setDefaultTimeout(25000); page.on('pageerror', e => errors.push(e.message));
      // Observe real browser streams so cleanup can be checked after DOM removal.
      await page.addInitScript(() => {
        window.capturedTracks = [];
        const capture = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
        navigator.mediaDevices.getUserMedia = async constraints => { const stream = await capture(constraints); window.capturedTracks.push(...stream.getTracks()); return stream; };
        window.screenTracks = [];
        const display = navigator.mediaDevices.getDisplayMedia.bind(navigator.mediaDevices);
        navigator.mediaDevices.getDisplayMedia = async constraints => { const stream = await display(constraints); window.screenTracks.push(...stream.getTracks()); return stream; };
      });
      await page.goto(`${frontend}/login`);
      await page.getByLabel('Email', { exact: true }).fill(account.email);
      await page.getByLabel('Mật khẩu', { exact: true }).fill(account.password);
      const login = page.waitForResponse(r => r.url().endsWith('/api/v1/auth/login') && r.request().method() === 'POST');
      await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
      account.token = (await (await login).json()).data.access_token;
      await page.getByRole('heading', { name: `Xin chào, Media ${account.role}` }).waitFor(); pages.push(page);
    }
    const [owner, member] = accounts; const [a, b] = pages;
    const workspace = await api(owner, 'POST', '/workspaces', { name: marker }, 201);
    const invitation = await api(owner, 'POST', `/workspaces/${workspace.id}/invitations`, { invitee_user_id: member.id }, 201);
    await api(member, 'POST', `/workspace-invitations/${invitation.token}/accept`);
    const study = await api(owner, 'POST', `/workspaces/${workspace.id}/channels`, { name: 'media-smoke', type: 'STUDY_ROOM' }, 201);
    for (const page of pages) {
      await page.goto(`${frontend}/workspaces/${workspace.id}`);
      await page.getByRole('button', { name: '◇ media-smoke STUDY_ROOM', exact: true }).click();
      await page.getByRole('button', { name: 'Tham gia phòng', exact: true }).click();
      await page.getByText('Đã kết nối media', { exact: true }).waitFor();
      assert.equal(await page.evaluate(() => window.capturedTracks.length), 0);
      assert.equal(await page.evaluate(() => window.screenTracks.length), 0);
    }
    console.log('PASS: two authenticated members connected; devices OFF without capture');
    const remote = b.getByRole('article', { name: 'Media Media owner', exact: true });
    if (screenTest) {
      const screen = remote.locator('[data-media-source="screen_share"] video');
      const remoteB = a.getByRole('article', { name: 'Media Media member', exact: true });
      const start = async page => {
        await page.getByRole('button', { name: 'Chia sẻ màn hình', exact: true }).click();
        await page.getByRole('button', { name: 'Dừng chia sẻ màn hình', exact: true }).waitFor();
      };
      const state = async (id, expected) => {
        const deadline = Date.now() + 10000;
        while (Date.now() < deadline) {
          const details = await api(member, 'GET', `/channels/${study.id}/study-room`);
          if (details.participants.find(p => p.user_id === id)?.screen_sharing === expected) return;
          await new Promise(resolve => setTimeout(resolve, 250));
        }
        throw new Error('Presence screen_sharing did not converge');
      };
      await start(a); await screen.waitFor();
      // Pixel evidence proves the selected browser tab is actually captured,
      // rather than Chrome's synthetic screen test pattern or a fake track.
      const expectColor = async (green, blue) => b.waitForFunction(({ green, blue }) => {
        const v = document.querySelector('[data-media-source="screen_share"] video');
        if (!v || v.readyState < 2 || !v.videoWidth) return false;
        const canvas = document.createElement('canvas'); canvas.width = 1; canvas.height = 1;
        const ctx = canvas.getContext('2d'); ctx.drawImage(v, v.videoWidth / 2, v.videoHeight / 2, 1, 1, 0, 0, 1, 1);
        const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
        return Math.abs(r - 20) < 25 && Math.abs(g - green) < 25 && Math.abs(b - blue) < 25;
      }, { green, blue });
      await expectColor(180, 80);
      await source.evaluate(() => { document.body.style.background = 'rgb(20,80,180)'; });
      await expectColor(80, 180); await state(owner.id, true);
      console.log('PASS UC26: real selected tab pixels and live color change decoded remotely; share state ON');
      await start(b); await remoteB.locator('[data-media-source="screen_share"] video').waitFor();
      await a.getByRole('button', { name: 'Dừng chia sẻ màn hình', exact: true }).click();
      await screen.waitFor({ state: 'detached' }); await state(owner.id, false); await state(member.id, true);
      assert.ok(await b.getByRole('button', { name: 'Dừng chia sẻ màn hình', exact: true }).isVisible());
      console.log('PASS UC26: simultaneous shares; stopping A preserves B');
      await source.close();
      await b.getByRole('button', { name: 'Chia sẻ màn hình', exact: true }).waitFor();
      await remoteB.locator('[data-media-source="screen_share"] video').waitFor({ state: 'detached' }); await state(member.id, false);
      console.log('PASS UC26: browser-ended source reconciles track, tile and socket state');
      await openSource();
      for (const action of ['leave', 'switch', 'disconnect']) {
        await start(a); await screen.waitFor();
        if (action === 'leave') await a.getByRole('button', { name: 'Rời phòng', exact: true }).click();
        if (action === 'switch') await a.getByRole('button', { name: '# general TEXT', exact: true }).click();
        if (action === 'disconnect') await contexts[screenTest ? 1 : 0].setOffline(true);
        await screen.waitFor({ state: 'detached' });
        await a.waitForFunction(() => window.screenTracks.every(t => t.readyState === 'ended'));
        if (action === 'disconnect') {
          await contexts[1].setOffline(false); await a.reload();
          await a.getByRole('button', { name: '◇ media-smoke STUDY_ROOM', exact: true }).click();
        }
        if (action === 'switch') await a.getByRole('button', { name: '◇ media-smoke STUDY_ROOM', exact: true }).click();
        await a.getByRole('button', { name: 'Tham gia phòng', exact: true }).click();
        await a.getByText('Đã kết nối media', { exact: true }).waitFor();
        console.log(`PASS UC26: ${action} cleans screen capture and remote tile; rejoin OFF`);
      }
    }
    await a.getByRole('button', { name: 'Camera: OFF', exact: true }).click();
    await a.getByRole('button', { name: 'Camera: ON', exact: true }).waitFor();
    await remote.locator('video').waitFor();
    await b.waitForFunction(() => [...document.querySelectorAll('article video')].some(v => v.videoWidth > 0 && v.readyState >= 2));
    await a.getByRole('button', { name: 'Microphone: OFF', exact: true }).click();
    await remote.locator('audio').waitFor({ state: 'attached' });
    await b.getByRole('button', { name: 'Cho phép phát âm thanh', exact: true }).click();
    await b.waitForFunction(() => [...document.querySelectorAll('audio')].some(a => !a.paused && a.currentTime > 0 && a.srcObject?.getAudioTracks().some(t => t.readyState === 'live')));
    await remote.getByText('Microphone: ON · Camera: ON', { exact: true }).waitFor();
    console.log('PASS: remote video decodes and audio track plays over real WebRTC');
    for (const device of ['Camera', 'Microphone']) await a.getByRole('button', { name: `${device}: ON`, exact: true }).click();
    await remote.locator('video').waitFor({ state: 'detached' }); await remote.locator('audio').waitFor({ state: 'detached' });
    await remote.getByText('Microphone: OFF · Camera: OFF', { exact: true }).waitFor();
    await a.waitForFunction(() => window.capturedTracks.every(t => t.readyState === 'ended'));
    console.log('PASS: unpublish removes remote tracks and stops local capture');
    await a.getByRole('button', { name: 'Camera: OFF', exact: true }).click(); await remote.locator('video').waitFor();
    await a.getByRole('button', { name: 'Rời phòng', exact: true }).click();
    await remote.waitFor({ state: 'detached' }); await a.waitForFunction(() => window.capturedTracks.every(t => t.readyState === 'ended'));
    console.log('PASS: leave cleans up media and remote participant');
    await a.getByRole('button', { name: 'Tham gia phòng', exact: true }).click(); await a.getByText('Đã kết nối media', { exact: true }).waitFor();
    await a.getByRole('button', { name: 'Camera: OFF', exact: true }).click(); await remote.locator('video').waitFor();
    await a.getByRole('button', { name: '# general TEXT', exact: true }).click();
    await remote.waitFor({ state: 'detached' }); await a.waitForFunction(() => window.capturedTracks.every(t => t.readyState === 'ended'));
    await a.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).waitFor();
    assert.deepEqual(errors, []); console.log('PASS: switching to TEXT unmounts media; no page errors');
  } finally {
    for (const context of contexts) await context.close();
    if (browser) await browser.close();
    const backendDir = path.resolve(__dirname, '../../backend');
    const result = spawnSync(process.env.LIVE_PYTHON || path.join(backendDir, '.venv-win/Scripts/python.exe'), ['-m', 'scripts.cleanup_media_live'], { cwd: backendDir, input: JSON.stringify({ marker }), encoding: 'utf8', timeout: 30000 });
    assert.equal(result.status, 0, 'Scoped fixture cleanup failed'); console.log(result.stdout.trim());
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
