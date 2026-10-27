(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const demo = !!BOOT.demo;
  let state = BOOT.state || {rows: [], checked: [], busy: false, cat: 'idle', answer: '', notice: $('notice').textContent};
  let font = BOOT.font;
  let sending = false;
  let version = 0;
  let tableSignature = '';
  let catState = 'idle';
  let catStart = performance.now();
  let lastFrame = -Infinity;
  // Owner wants the cat to move even when Windows animation effects are off, so reduced-motion is not applied to it.
  const play = new CatMotion.Play(BOOT.play);
  const asset = path => BOOT.asset_base + path + BOOT.auth;
  const key = new URLSearchParams(BOOT.auth).get('key');
  const labels = {idle: '待機中', walk: '処理中', done: '完了', error: '要確認'};

  function setFont() { $('title').style.fontFamily = `title${font}, sans-serif`; }
  setFont();
  $('title').addEventListener('click', () => { font = (font + 1) % BOOT.fonts.length; setFont(); });
  // SVG favicon uses the same original book and pen symbol as the masthead.
  const symbol = document.getElementById('icon-app');
  const favicon = document.createElement('link');
  favicon.rel = 'icon';
  favicon.href = 'data:image/svg+xml,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">${symbol.innerHTML}</svg>`);
  document.head.append(favicon);

  function updateImage(img, path) {
    const url = asset(path);
    if (img.getAttribute('src') !== url) img.src = url;
    img.hidden = false;
  }
  if (BOOT.play) {
    const [x, y] = BOOT.play.cursor.hotspot;
    document.body.style.setProperty('--teaser', `url("${asset('cat_play/cursor/teaser_32.png')}") ${x} ${y}`);
    document.body.classList.add('teaser');
    document.addEventListener('pointermove', event => {
      const box = $('face-stage').getBoundingClientRect();
      play.pointer(event.clientX - (box.left + box.width / 2), event.clientY - (box.top + box.height / 2), performance.now());
    });
  }
  for (const id of ['body-cat', 'face-cat']) $(id).addEventListener('error', () => { $(id).hidden = true; });
  function animate(now) {
    if (BOOT.sprites && now - lastFrame > 45) {
      lastFrame = now;
      const elapsed = now - catStart;
      // After done/error has been shown for a while the body cat goes back to its idle loop; the badge keeps the status.
      const bodyState = ['done', 'error'].includes(catState) && elapsed > 8000 ? 'idle' : catState;
      const spec = BOOT.sprites.states[bodyState] || BOOT.sprites.states.idle;
      const index = CatMotion.frameAt(spec, bodyState === catState ? elapsed : elapsed - 8000);
      updateImage($('body-cat'), `cat_sprites/${bodyState}/${bodyState}_${String(index).padStart(2, '0')}.png`);
      $('body-cat').style.right = catState === 'walk' ? `${CatMotion.bodyOffset(elapsed, $('body-cat').parentElement.clientWidth)}px` : '20px';
      const face = BOOT.sprites.face;
      const playing = play.sample(now);
      let width, height;
      if (playing) {
        const {group, index: i} = playing;
        updateImage($('face-cat'), `cat_play/${group}/${group}_${String(i).padStart(2, '0')}.png`);
        width = BOOT.play.frame_width; height = BOOT.play.frame_height;
      } else if (BOOT.play) {
        // The playable close-up looks straight ahead when idle; the state badge shows the status.
        updateImage($('face-cat'), 'cat_play/look/look_02.png');
        width = BOOT.play.frame_width; height = BOOT.play.frame_height;
      } else {
        const i = CatMotion.frameAt(face.states[catState] || face.states.idle, elapsed);
        updateImage($('face-cat'), `cat_sprites/face/${catState}/face_${catState}_${String(i).padStart(2, '0')}.png`);
        width = face.frame_width; height = face.frame_height;
      }
      $('face-cat').dataset.frame = `${width}x${height}`;
    }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);

  function render(next) {
    state = next;
    $('notice').textContent = state.notice;
    $('row-count').textContent = `${state.rows.length}本`;
    const checked = new Set(state.checked);
    const count = state.rows.filter(r => checked.has(r.id)).length;
    $('selection-count').textContent = `チェック ${count}本`;
    $('check-all').checked = state.rows.length > 0 && count === state.rows.length;
    $('check-all').indeterminate = count > 0 && count < state.rows.length;
    const signature = JSON.stringify([state.rows, state.checked, state.busy]);
    if (signature !== tableSignature) {
      tableSignature = signature;
      const focusId = document.activeElement?.dataset?.id;
      const fragment = document.createDocumentFragment();
      for (const row of state.rows) {
        const tr = document.createElement('tr');
        tr.classList.toggle('checked', checked.has(row.id)); tr.dataset.status = row.status;
        const cell = document.createElement('td');
        const checkbox = document.createElement('input'); checkbox.type = 'checkbox';
        checkbox.checked = checked.has(row.id); checkbox.disabled = state.busy;
        checkbox.dataset.id = row.id;
        checkbox.setAttribute('aria-label', `選択：${row.cells[0].full}`);
        checkbox.addEventListener('change', () => operate({action: 'check', id: row.id}));
        cell.append(checkbox); tr.append(cell);
        row.cells.forEach((value, i) => {
          const td = document.createElement('td'); td.title = value.full;
          const span = document.createElement(i === 0 && row.url ? 'a' : 'span'); span.textContent = value.text;
          if (i === 0 && row.url) {
            // Title opens the video in the normal browser; the app window stays as is.
            span.href = row.url; span.target = '_blank'; span.rel = 'noopener noreferrer'; span.className = 'title-link';
            if (row.translate) { td.removeAttribute('title'); attachTranslation(span, row); }
          }
          td.append(span); tr.append(td);
        });
        fragment.append(tr);
      }
      $('rows').replaceChildren(fragment);
      if (focusId) Array.from($('rows').querySelectorAll('input')).find(input => input.dataset.id === focusId)?.focus();
    }
    $('empty').hidden = state.rows.length > 0;
    $('answer').textContent = state.answer || (state.busy ? '処理中です…' : 'ここに回答が表示されます。');
    if (state.cat !== catState) { catState = state.cat; catStart = performance.now(); }
    $('cat-state').textContent = labels[catState]; $('cat-state').dataset.state = catState;
    $('grok-reason').textContent = BOOT.grok_reason;
    $('grok').title = BOOT.grok_reason;
    lockControls();
  }
  const translations = new Map();
  const tip = document.createElement('div'); tip.id = 'title-tip'; tip.hidden = true; tip.setAttribute('role', 'tooltip');
  document.body.append(tip);
  function placeTip(target) {
    const box = target.getBoundingClientRect();
    tip.style.left = `${Math.max(8, Math.min(box.left, innerWidth - 520))}px`;
    tip.style.top = `${box.bottom + 6}px`;
  }
  function attachTranslation(link, row) {
    let timer = null;
    const show = () => {
      placeTip(link); tip.hidden = false;
      const known = translations.get(row.id);
      tip.innerHTML = '';
      const original = document.createElement('div'); original.className = 'tip-original'; original.textContent = row.cells[0].full;
      const ja = document.createElement('div'); ja.className = 'tip-ja';
      tip.append(original, ja);
      if (known) { ja.textContent = known; return; }
      if (demo) { ja.textContent = '（日本語訳はアプリで表示されます）'; return; }
      ja.textContent = '日本語に訳しています…';
      request('/api/translate', {id: row.id}).then(body => {
        translations.set(row.id, body.ja);
        if (!tip.hidden) ja.textContent = body.ja;
      }).catch(error => { if (!tip.hidden) ja.textContent = error.message; });
    };
    link.addEventListener('pointerenter', () => { clearTimeout(timer); timer = setTimeout(show, 350); });
    link.addEventListener('pointerleave', () => { clearTimeout(timer); tip.hidden = true; });
    link.addEventListener('focus', show);
    link.addEventListener('blur', () => { tip.hidden = true; });
  }
  function lockControls() {
    document.querySelectorAll('[data-action], #check-all, #show-rejected, #show-processed, #send-question, #rows input').forEach(el => { el.disabled = state.busy || sending; });
  }
  async function request(path, data) {
    const response = await fetch(path + BOOT.auth, {
      method: data ? 'POST' : 'GET', cache: 'no-store', credentials: 'omit',
      headers: data ? {'Content-Type': 'application/json', 'X-App-Key': key} : {},
      ...(data ? {body: JSON.stringify(data)} : {})
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || '要求を確認できません（UNKNOWN）。');
    return body;
  }
  function demoOperation(data) {
    const visible = new Set(state.rows.map(r => r.id));
    const selected = new Set(state.checked);
    if (data.action === 'check') { selected.has(data.id) ? selected.delete(data.id) : selected.add(data.id); }
    if (data.action === 'check_all') {
      const all = [...visible].every(id => selected.has(id));
      visible.forEach(id => all ? selected.delete(id) : selected.add(id));
    }
    state.checked = [...selected];
    state.notice = ['check', 'check_all'].includes(data.action) ? '確認用の静止ページです。保存・外部通信は行いません。' : '確認用の静止ページです。実際の操作はアプリから行ってください。';
    render(state);
  }
  async function operate(data) {
    if (sending || state.busy) return;
    if (demo) { demoOperation(data); return; }
    sending = true; lockControls();
    const serial = ++version;
    try {
      const next = await request('/api/action', data);
      if (serial === version) render(next);
      if (data.action === 'manual' && next.busy) $('urls').value = '';
    } catch (error) { $('notice').textContent = error.message; }
    finally { sending = false; lockControls(); }
  }
  document.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', () => operate({
    action: button.dataset.action, reason: $('reject-reason').value, urls: $('urls').value, correction: $('correction').value
  })));
  $('check-all').addEventListener('change', () => operate({action: 'check_all'}));
  for (const id of ['show-rejected', 'show-processed']) $(id).addEventListener('change', () => operate({action: 'filters', rejected: $('show-rejected').checked, processed: $('show-processed').checked}));
  $('open-question').addEventListener('click', () => { $('question-panel').showModal(); $('question').focus(); });
  $('close-question').addEventListener('click', () => $('question-panel').close());
  $('send-question').addEventListener('click', () => {
    const question = $('question').value.trim();
    if (!question || question.length > 2000) { $('answer').textContent = '質問は1〜2000文字で入力してください。'; return; }
    operate({action: 'ask', question});
  });
  render(state);
  if (!demo) {
    const heartbeat = () => request('/api/heartbeat', {}).catch(() => { $('notice').textContent = '接続を確認できません（UNKNOWN）。操作を再送せず、状態を確認してください。'; });
    heartbeat(); setInterval(heartbeat, 2500);
    async function poll() {
      if (!sending) {
        const serial = ++version;
        try { const next = await request('/api/state'); if (serial === version) render(next); }
        catch (_) { $('notice').textContent = '接続を確認できません（UNKNOWN）。画面を開き直してください。'; }
      }
      setTimeout(poll, 1000);
    }
    poll();
  }
})();
