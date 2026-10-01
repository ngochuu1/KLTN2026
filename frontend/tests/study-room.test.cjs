const { test, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
require.extensions['.ts'] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, filename);
const { connectRoom } = require('../src/features/study-room/realtime.ts');
const { createMedia } = require('../src/features/study-room/media.ts');
const { RoomEvent, Track } = require('livekit-client');
const { EventEmitter } = require('node:events');
const originalSocket = global.WebSocket;
const originalBase = process.env.NEXT_PUBLIC_API_BASE_URL;
afterEach(() => { global.WebSocket = originalSocket; if (originalBase === undefined) delete process.env.NEXT_PUBLIC_API_BASE_URL; else process.env.NEXT_PUBLIC_API_BASE_URL = originalBase; });
function fixture(t, auth = { getToken: () => 'test-token', refresh: async () => 'refreshed' }) {
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://backend.example';
  const sockets = [], timers = [], intervals = [], states = [], errors = [];
  t.mock.method(global, 'setTimeout', callback => { const timer = { callback }; timers.push(timer); return timer; });
  t.mock.method(global, 'clearTimeout', timer => { if (timer) timer.canceled = true; });
  t.mock.method(global, 'setInterval', callback => { const timer = { callback }; intervals.push(timer); return timer; });
  t.mock.method(global, 'clearInterval', timer => { if (timer) timer.canceled = true; });
  global.WebSocket = class {
    static OPEN = 1;
    readyState = 1; frames = [];
    constructor(url) { this.url = url; sockets.push(this); }
    send(text) { this.frames.push(JSON.parse(text)); }
    close() { this.closed = true; }
  };
  const client = connectRoom('room', auth, state => states.push(state), error => errors.push(error));
  return { client, sockets, timers, intervals, states, errors };
}
test('room authenticates, receives authoritative state, sends join/leave and cleans up', t => {
  const f = fixture(t), ws = f.sockets[0];
  assert.equal(f.states.length, 0); // UI remains loading before server acknowledgement.
  assert.equal(String(ws.url), 'ws://backend.example/api/v1/ws/study-rooms/room');
  ws.onopen(); assert.deepEqual(ws.frames[0], { type: 'auth', access_token: 'test-token' });
  f.client.command('join');
  assert.equal(f.states.length, 0);
  ws.onmessage({ data: JSON.stringify({ type: 'room.state', data: { self_state: 'IN_ROOM', participants: [] } }) });
  assert.equal(f.states[0].self_state, 'IN_ROOM');
  f.intervals[0].callback(); f.client.command('leave');
  assert.deepEqual(ws.frames.slice(1).map(frame => frame.type), ['join', 'state', 'leave']);
  f.client.close(); assert.ok(ws.closed); assert.ok(f.intervals.every(timer => timer.canceled)); assert.ok(f.timers.every(timer => timer.canceled));
  ws.onmessage({ data: JSON.stringify({ type: 'room.state', data: {} }) });
  assert.equal(f.states.length, 1);
});
test('forbidden stops connection and watchdog reports unresponsive server', async t => {
  const f = fixture(t);
  f.timers[0].callback(); assert.ok(f.sockets[0].closed); assert.equal(f.errors.length, 1);
  await f.sockets[0].onclose({ code: 4403 });
  assert.match(f.errors.at(-1), /Không có quyền/); assert.equal(f.sockets.length, 1);
  f.client.close();
});
test('disposing while token refresh is pending prevents reconnect', async t => {
  let resolve;
  const f = fixture(t, { getToken: () => 'old', refresh: () => new Promise(done => { resolve = done; }) });
  const pending = f.sockets[0].onclose({ code: 4401 });
  f.client.close(); resolve('new'); await pending;
  assert.equal(f.sockets.length, 1); assert.equal(f.errors.length, 1);
});

test('device command sends boolean patch without identity and waits for authoritative snapshot', t => {
  const f = fixture(t), ws = f.sockets[0];
  f.client.devices({ microphone_enabled: true });
  f.client.devices({ camera_enabled: false });
  assert.deepEqual(ws.frames, [{ type: 'devices', microphone_enabled: true }, { type: 'devices', camera_enabled: false }]);
  assert.equal(f.states.length, 0);
  const state = { self_state: 'IN_ROOM', self_devices: { microphone_enabled: true, camera_enabled: false }, participants: [{ user_id: 'other', microphone_enabled: false, camera_enabled: true }] };
  ws.onmessage({ data: JSON.stringify({ type: 'room.state', data: state }) });
  assert.deepEqual(f.states[0], state);
  f.client.close(); f.client.devices({ camera_enabled: true });
  assert.equal(ws.frames.length, 2);
});

function mediaFixture(options = {}) {
  const room = new EventEmitter();
  const states = [], errors = [], tracks = [];
  let disconnected = 0, captures = 0;
  room.remoteParticipants = new Map();
  room.localParticipant = { identity: 'self', name: 'Self', trackPublications: new Map(),
    async publishTrack(track, { source }) {
      if (options.publish) await options.publish();
      this.trackPublications.set(source, { source, track, isMuted: false }); room.emit(RoomEvent.LocalTrackPublished);
    },
    async unpublishTrack(track) {
      for (const [key, publication] of this.trackPublications) if (publication.track === track) this.trackPublications.delete(key);
      room.emit(RoomEvent.LocalTrackUnpublished);
    },
  };
  room.connect = options.connect || (async () => {});
  room.disconnect = async () => { room.closed = true; };
  room.startAudio = async () => {};
  async function capture() {
    captures++;
    if (options.capture) return options.capture();
    const stream = new EventTarget(); stream.readyState = 'live';
    const track = { mediaStreamTrack: stream, stop() { stream.readyState = 'ended'; this.stopped = true; } };
    tracks.push(track); return track;
  }
  const media = createMedia(options.credential || (async () => ({ url: 'ws://test', token: 'test' })), s => states.push(s), e => errors.push(e), () => disconnected++, { room: () => room, audio: capture, video: capture, screen: capture });
  return { room, media, states, errors, tracks, captures: () => captures, disconnected: () => disconnected };
}

test('media joins with devices OFF, publishes/unpublishes and derives remote state from tracks', async () => {
  const f = mediaFixture(); await f.media.connect();
  assert.equal(f.captures(), 0); assert.ok(f.states.at(-1).connected);
  for (const [device, source] of [['microphone_enabled', Track.Source.Microphone], ['camera_enabled', Track.Source.Camera]]) {
    await f.media.toggle(device, true); await f.media.toggle(device, true);
    assert.equal(f.states.at(-1).participants[0][device], true);
    const track = f.room.localParticipant.trackPublications.get(source).track;
    f.room.remoteParticipants.set('other', { identity: 'other', name: 'Other', trackPublications: new Map([[source, { source, track, isMuted: false }]]) });
    f.room.emit(RoomEvent.TrackSubscribed);
    assert.equal(f.states.at(-1).participants[1][device], true);
    await f.media.toggle(device, false); assert.ok(track.stopped);
    assert.equal(f.states.at(-1).participants[0][device], false);
  }
  assert.equal(f.captures(), 2); f.media.close(); assert.ok(f.room.closed);
});

test('permission/device denial keeps media connected and device OFF', async () => {
  for (const name of ['NotAllowedError', 'NotFoundError', 'NotReadableError']) {
    const f = mediaFixture({ capture: async () => { throw new DOMException('denied', name); } });
    await f.media.connect(); await f.media.toggle('camera_enabled', true);
    assert.match(f.errors.at(-1), /quyền truy cập/);
    assert.equal(f.states.at(-1).participants[0].camera_enabled, false);
    assert.ok(f.states.at(-1).connected); f.media.close();
  }
});

test('remote unsubscribe reads publications after LiveKit clears the old track', async () => {
  const f = mediaFixture(); await f.media.connect();
  const publication = { source: Track.Source.Microphone, isMuted: false, track: { mediaStreamTrack: { readyState: 'live' } } };
  const publications = new Map([['audio', publication]]);
  f.room.remoteParticipants.set('other', { identity: 'other', name: 'Other', trackPublications: publications });
  f.room.emit(RoomEvent.TrackSubscribed);
  assert.equal(f.states.at(-1).participants[1].microphone_enabled, true);
  // LiveKit 2.17.2 emits before setTrack(undefined) and map deletion.
  f.room.emit(RoomEvent.TrackUnsubscribed, publication.track, publication);
  publication.track = undefined; publications.clear();
  await Promise.resolve();
  assert.equal(f.states.at(-1).participants[1].microphone_enabled, false);
  assert.equal(f.states.at(-1).participants[1].tracks.length, 0);
  f.media.close();
});

test('unmount during pending capture stops late track without publishing', async () => {
  let resolve;
  const track = { stop() { this.stopped = true; } };
  const f = mediaFixture({ capture: () => new Promise(done => { resolve = done; }) });
  await f.media.connect(); const pending = f.media.toggle('camera_enabled', true);
  f.media.close(); resolve(track); await pending;
  assert.ok(track.stopped); assert.equal(f.room.localParticipant.trackPublications.size, 0);
});

test('publish failure stops capture; device-ended and disconnect clean up', async () => {
  const failed = mediaFixture({ publish: async () => { throw new Error('publish failed'); } });
  await failed.media.connect(); await failed.media.toggle('microphone_enabled', true);
  assert.ok(failed.tracks[0].stopped); assert.equal(failed.room.localParticipant.trackPublications.size, 0); failed.media.close();
  const f = mediaFixture(); await f.media.connect(); await f.media.toggle('camera_enabled', true);
  f.tracks[0].mediaStreamTrack.dispatchEvent(new Event('ended'));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(f.states.at(-1).participants[0].camera_enabled, false);
  await f.media.toggle('microphone_enabled', true); f.room.emit(RoomEvent.Disconnected);
  assert.ok(f.tracks.every(t => t.stopped)); assert.equal(f.disconnected(), 1);
});

test('credential/connect failure and dispose during credential request do not capture', async () => {
  const f = mediaFixture({ credential: async () => { throw new Error('403'); } });
  await f.media.connect(); assert.equal(f.disconnected(), 1); assert.equal(f.captures(), 0);
  let resolve, connections = 0;
  const delayed = mediaFixture({ credential: () => new Promise(done => { resolve = done; }), connect: async () => { connections++; } });
  const pending = delayed.media.connect(); delayed.media.close(); resolve({ url: 'ws://test', token: 'test' }); await pending;
  assert.equal(connections, 0);
});

test('screen publication is separate from camera and repeated start does not capture twice', async () => {
  const f = mediaFixture(); await f.media.connect(); assert.equal(f.captures(), 0);
  await f.media.toggle('camera_enabled', true);
  await f.media.toggle('screen_sharing', true); await f.media.toggle('screen_sharing', true);
  assert.equal(f.captures(), 2);
  assert.ok(f.room.localParticipant.trackPublications.has(Track.Source.ScreenShare));
  assert.ok(f.states.at(-1).participants[0].screen_sharing);
  await f.media.toggle('screen_sharing', false);
  assert.ok(f.tracks[1].stopped); assert.equal(f.tracks[0].stopped, undefined);
  assert.ok(f.states.at(-1).participants[0].camera_enabled);
  assert.equal(f.states.at(-1).participants[0].screen_sharing, false); f.media.close();
});

test('screen cancellation, unsupported capture and failed publication leave state OFF', async () => {
  for (const options of [
    { capture: async () => { throw new DOMException('cancel', 'NotAllowedError'); } },
    { capture: async () => { throw new TypeError('getDisplayMedia unsupported'); } },
    { publish: async () => { throw new Error('publish denied'); } },
  ]) {
    const f = mediaFixture(options); await f.media.connect(); await f.media.toggle('screen_sharing', true);
    assert.equal(f.states.at(-1).participants[0].screen_sharing, false);
    assert.match(f.errors.at(-1), /Không thể chia sẻ màn hình/);
    assert.ok(f.tracks.every(t => t.stopped)); f.media.close();
  }
});

test('browser-ended screen capture and media disconnect stop screen without stopping another user', async () => {
  const f = mediaFixture(); await f.media.connect(); await f.media.toggle('screen_sharing', true);
  const remoteTrack = { mediaStreamTrack: { readyState: 'live' } };
  f.room.remoteParticipants.set('other', { identity: 'other', trackPublications: new Map([['screen', { source: Track.Source.ScreenShare, track: remoteTrack }]]) });
  f.room.emit(RoomEvent.TrackSubscribed);
  f.tracks[0].mediaStreamTrack.dispatchEvent(new Event('ended'));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(f.states.at(-1).participants[0].screen_sharing, false);
  assert.equal(f.states.at(-1).participants[1].screen_sharing, true);
  await f.media.toggle('screen_sharing', true); f.room.emit(RoomEvent.Disconnected);
  assert.ok(f.tracks.every(t => t.stopped)); assert.equal(f.disconnected(), 1);
});

test('pending screen picker cannot duplicate or publish after leaving', async () => {
  let resolve; const track = { stop() { this.stopped = true; } };
  const f = mediaFixture({ capture: () => new Promise(done => { resolve = done; }) });
  await f.media.connect(); const start = f.media.toggle('screen_sharing', true);
  await f.media.toggle('screen_sharing', true); assert.equal(f.captures(), 1);
  f.media.close(); resolve(track); await start;
  assert.ok(track.stopped); assert.equal(f.room.localParticipant.trackPublications.size, 0);
});
