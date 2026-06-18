/* =========================================================
   IET Strathmore — Admin Dashboard
   All data loaded from / saved to the Django API.
   ========================================================= */
(function () {
  'use strict';

  /* ---------- CSRF ---------- */
  function getCookie(name) {
    const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return m ? decodeURIComponent(m[2]) : '';
  }
  const CSRF = getCookie('csrftoken');

  /* ---------- STATE ---------- */
  let OFFICIALS = [];
  let EVENTS = [];
  let MEMBERS = [];
  let GALLERY = [];
  let ANNOUNCEMENTS = [];

  /* ---------- ICONS ---------- */
  const ICONS = {
    pencil: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg>',
    trash:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><rect x="5" y="6" width="14" height="15" rx="2"/><path d="M10 11v6M14 11v6"/></svg>',
    assign: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"/><path d="M3 19c.7-3 3.2-5 6-5"/><path d="M16 13v6M13 16h6"/></svg>',
    event:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18"/></svg>',
    mail:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
    user:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c1-3 4-5 8-5s7 2 8 5"/></svg>',
    image:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="14" rx="2"/><circle cx="8.5" cy="9" r="1.5"/><path d="m3 16 4-3 4 3 5-5 5 4"/></svg>',
  };

  /* ---------- HELPERS ---------- */
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  function escHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function fmtDate(iso, timeStr) {
    const dt = new Date(iso + 'T' + (timeStr || '00:00'));
    return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function fmtDateTime(isoStr) {
    const dt = new Date(isoStr);
    return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function getToggleVal(name) {
    const active = document.querySelector(`.toggle-group[data-toggle="${name}"] .toggle-opt.is-active`);
    return active ? active.dataset.val : '';
  }

  function avatarHTML(initials, size, title) {
    return `<span class="avatar${size ? ' avatar--' + size : ''}" title="${title || ''}"><span>${initials}</span></span>`;
  }

  function assigneeStack(assignments) {
    const visible = assignments.slice(0, 3);
    const more = assignments.length - visible.length;
    let html = '<div class="assignees">';
    visible.forEach(a => { html += avatarHTML(a.initials, '', a.official_name); });
    if (more > 0) html += `<span class="assignees__more">+${more}</span>`;
    html += '</div>';
    return html;
  }

  /* ---------- API FETCH ---------- */
  async function apiFetch(url, opts = {}) {
    const { headers: extraHeaders, ...restOpts } = opts;
    const res = await fetch(url, {
      headers: { 'X-CSRFToken': CSRF, ...(extraHeaders || {}) },
      ...restOpts,
    });
    return res;
  }

  /* =====================================================
     STATS
  ===================================================== */
  async function loadStats() {
    try {
      const res = await apiFetch('/api/stats/');
      if (!res.ok) return;
      const s = await res.json();

      // Dashboard overview cards
      setText('dashStatEvents', s.total_events);
      setText('dashStatUpcoming', s.upcoming_events);
      setText('dashStatMembers', s.active_members);
      setText('dashStatOfficials', s.active_officials);

      // Events section cards
      setText('evtStatTotal', s.total_events);
      setText('evtStatUpcoming', s.upcoming_events);
      setText('evtStatPast', s.past_events);
      setText('evtStatMembers', s.active_members);

      // Members section cards
      setText('memStatTotal', s.total_members);
      setText('memStatActive', s.active_members);
      setText('memStatNew', s.new_members_this_month);

      // Dashboard upcoming delta
      const upEl = document.getElementById('dashStatUpcomingDelta');
      if (upEl) upEl.textContent = s.upcoming_events ? `Next event scheduled` : 'None scheduled';

      const evtUpEl = document.getElementById('evtStatUpcomingDelta');
      if (evtUpEl) evtUpEl.textContent = s.upcoming_events ? 'Scheduled soon' : 'None scheduled';
    } catch (e) { /* silent */ }
  }

  /* =====================================================
     EVENTS
  ===================================================== */
  async function loadEvents() {
    try {
      const res = await apiFetch('/api/events/');
      if (!res.ok) return;
      EVENTS = await res.json();
      renderEvents();
      updatePillCounts();
    } catch (e) { /* silent */ }
  }

  let activeFilter = 'all';

  function renderEvents() {
    const rows = activeFilter === 'all'
      ? EVENTS
      : EVENTS.filter(e => e.temporal_status === activeFilter);

    const tbody = $('#eventsBody');
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:#9a8a9c;">
        No events yet. Click <strong>Create New Event</strong> to add one.
      </td></tr>`;
      return;
    }

    tbody.innerHTML = rows.map(e => `
      <tr data-id="${e.id}">
        <td>
          <div class="row-title">
            <span class="row-title__thumb">${ICONS.event}</span>
            <div class="row-title__main">
              <strong>${escHtml(e.title)}</strong>
              <span>${escHtml(e.description.slice(0, 60))}${e.description.length > 60 ? '…' : ''}</span>
            </div>
          </div>
        </td>
        <td>
          <div class="date-cell">
            <strong>${fmtDate(e.date, e.time)}</strong>
            <span>${e.time || '—'}</span>
          </div>
        </td>
        <td><span class="type-tag">${e.event_type}</span></td>
        <td><span class="status status--${e.temporal_status.toLowerCase()}">${e.temporal_status}</span></td>
        <td>${assigneeStack(e.assignments)}</td>
        <td>
          <div class="actions">
            <button class="action-btn" data-act="edit"   title="Edit event">${ICONS.pencil}</button>
            <button class="action-btn action-btn--danger" data-act="delete" title="Delete event">${ICONS.trash}</button>
          </div>
        </td>
      </tr>`).join('');
  }

  function updatePillCounts() {
    setText('pilAll', EVENTS.length);
    setText('pilUpcoming', EVENTS.filter(e => e.temporal_status === 'Upcoming').length);
    setText('pilOngoing', EVENTS.filter(e => e.temporal_status === 'Ongoing').length);
    setText('pilPast', EVENTS.filter(e => e.temporal_status === 'Past').length);
    updateEventsBadge();
  }

  function updateEventsBadge() {
    const badge = document.getElementById('navBadgeEvents');
    if (!badge) return;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const weekEnd = new Date(today);
    weekEnd.setDate(today.getDate() + (6 - today.getDay()) + 1); // end of this Sunday
    const thisWeek = EVENTS.filter(e => {
      const d = new Date(e.date + 'T00:00:00');
      return d >= today && d < weekEnd;
    });
    if (thisWeek.length) {
      badge.textContent = thisWeek.length;
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  }

  $$('.filter-pills .pill').forEach(p => {
    p.addEventListener('click', () => {
      $$('.filter-pills .pill').forEach(x => x.classList.remove('is-active'));
      p.classList.add('is-active');
      activeFilter = p.dataset.filter;
      renderEvents();
    });
  });

  /* ---------- Event Modal ---------- */
  let editingEventId = null;
  let pendingAssignments = [];

  function populateAssignSelect() {
    const sel = $('#assignPerson');
    const assigned = new Set(pendingAssignments.map(a => a.official_id));
    sel.innerHTML = '<option value="">— Select official —</option>' +
      OFFICIALS.filter(o => o.is_active && !assigned.has(o.id))
        .map(o => `<option value="${o.id}">${escHtml(o.full_name)} · ${escHtml(o.role_title)}</option>`)
        .join('');
  }

  function renderAssignTable() {
    const tbody = $('#assignBody');
    if (!pendingAssignments.length) {
      tbody.innerHTML = '<tr class="assign__empty"><td colspan="3">No assignments yet.</td></tr>';
      return;
    }
    tbody.innerHTML = pendingAssignments.map((a, i) => `
      <tr>
        <td>${escHtml(a.official_name)}</td>
        <td>${escHtml(a.role)}</td>
        <td><button type="button" class="assign-remove" data-remove="${i}" aria-label="Remove">×</button></td>
      </tr>`).join('');
  }

  function openEventModal(evt) {
    if (evt) {
      editingEventId = evt.id;
      $('#modalEventTitle').textContent = 'Edit Event';
      $('#evtTitle').value = evt.title;
      $('#evtType').value = evt.event_type;
      $('#evtDate').value = evt.date;
      $('#evtTime').value = evt.time || '';
      $('#evtVenue').value = evt.venue || '';
      $('#evtDesc').value = evt.description || '';
      pendingAssignments = evt.assignments.map(a => ({ ...a }));
      setToggle('status', evt.status);
      setToggle('visibility', evt.show_on_landing ? 'Show' : 'Hide');
    } else {
      editingEventId = null;
      $('#modalEventTitle').textContent = 'Create New Event';
      $('#eventForm').reset();
      pendingAssignments = [];
      setToggle('status', 'Published');
      setToggle('visibility', 'Show');
    }
    populateAssignSelect();
    renderAssignTable();
    openModal('modalEvent');
  }

  $('#openCreateEvent').addEventListener('click', () => openEventModal(null));

  $('#addAssignment').addEventListener('click', () => {
    const sel = $('#assignPerson');
    const id = parseInt(sel.value, 10);
    if (!id) return;
    const official = OFFICIALS.find(o => o.id === id);
    if (!official) return;
    const role = $('#assignRole').value;
    pendingAssignments.push({ official_id: id, official_name: official.full_name, initials: official.initials, role });
    populateAssignSelect();
    renderAssignTable();
  });

  $('#assignBody').addEventListener('click', e => {
    const btn = e.target.closest('[data-remove]');
    if (!btn) return;
    pendingAssignments.splice(parseInt(btn.dataset.remove, 10), 1);
    populateAssignSelect();
    renderAssignTable();
  });

  $('#saveEvent').addEventListener('click', async () => {
    const title = $('#evtTitle').value.trim();
    if (!title) { alert('Please enter an event title.'); return; }
    const date = $('#evtDate').value;
    if (!date) { alert('Please select a date.'); return; }

    const fd = new FormData();
    fd.append('title', title);
    fd.append('event_type', $('#evtType').value);
    fd.append('date', date);
    fd.append('time', $('#evtTime').value);
    fd.append('venue', $('#evtVenue').value.trim());
    fd.append('description', $('#evtDesc').value.trim());
    fd.append('status', getToggleVal('status') || 'Draft');
    fd.append('show_on_landing', getToggleVal('visibility') === 'Show' ? '1' : '0');
    const imgFile = $('#dropzone input[type=file]').files[0];
    if (imgFile) fd.append('cover_image', imgFile);
    fd.append('assignments', JSON.stringify(pendingAssignments));

    const url = editingEventId ? `/api/events/${editingEventId}/` : '/api/events/';
    const btn = $('#saveEvent');
    btn.disabled = true;
    btn.textContent = 'Saving…';
    try {
      const res = await apiFetch(url, { method: 'POST', body: fd });
      if (res.ok) {
        closeModal('modalEvent');
        await Promise.all([loadEvents(), loadStats()]);
      } else {
        const d = await res.json();
        alert('Error: ' + (d.error || 'Could not save event.'));
      }
    } finally {
      btn.disabled = false;
      btn.textContent = 'Save Event';
    }
  });

  /* ---------- Event table actions ---------- */
  let pendingDeleteId = null;
  let pendingDeleteType = null;

  $('#eventsBody').addEventListener('click', e => {
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const id = parseInt(btn.closest('tr').dataset.id, 10);
    const evt = EVENTS.find(x => x.id === id);
    if (!evt) return;
    if (btn.dataset.act === 'edit') {
      openEventModal(evt);
    } else if (btn.dataset.act === 'delete') {
      pendingDeleteId = id;
      pendingDeleteType = 'event';
      $('#deleteTitle').textContent = `Delete "${evt.title}"?`;
      openModal('modalDelete');
    }
  });

  /* =====================================================
     OFFICIALS
  ===================================================== */
  async function loadOfficials() {
    try {
      const res = await apiFetch('/api/officials/');
      if (!res.ok) return;
      OFFICIALS = await res.json();
      renderOfficials();
    } catch (e) { /* silent */ }
  }

  function renderOfficials() {
    const active   = OFFICIALS.filter(o => o.is_active).length;
    const inactive = OFFICIALS.filter(o => !o.is_active).length;
    setText('offCountActive',   active);
    setText('offCountInactive', inactive);
    const sub = document.getElementById('officialsSubtitle');
    if (sub) sub.textContent = `${OFFICIALS.length} officer${OFFICIALS.length === 1 ? '' : 's'} · 2025/26 chapter committee.`;

    const grid = $('#officialsGrid');
    if (!OFFICIALS.length) {
      grid.innerHTML = `<div class="empty-card" style="grid-column:1/-1">
        <h3>No officials yet</h3>
        <p>Click <strong>Add Official</strong> to register the first committee member.</p>
      </div>`;
      return;
    }
    grid.innerHTML = OFFICIALS.map(o => `
      <article class="off-card" data-id="${o.id}">
        <div class="off-card__head">
          ${o.photo
            ? `<div class="off-photo" title="${escHtml(o.full_name)}"><img src="${o.photo}" alt="${escHtml(o.full_name)}" /></div>`
            : avatarHTML(o.initials, 'md', o.full_name)}
          <div class="off-card__id">
            <strong>${escHtml(o.full_name)}</strong>
            <span>${escHtml(o.role_title)}</span>
          </div>
        </div>
        <div class="off-card__email">${ICONS.mail}<span>${escHtml(o.email)}</span></div>
        <span class="off-card__assign">${o.active_assignments} active assignment${o.active_assignments === 1 ? '' : 's'}</span>
        <span class="off-card__perm">Permissions · ${o.permission_level}</span>
        <div class="off-card__actions">
          <button class="btn btn--ghost" data-off-edit="${o.id}">Edit Profile</button>
          <button class="btn btn--ghost btn--danger-outline" data-off-delete="${o.id}">Remove</button>
        </div>
      </article>`).join('');
  }

  /* ---------- Official Modal ---------- */
  let editingOfficialId = null;

  function openOfficialModal(off) {
    if (off) {
      editingOfficialId = off.id;
      $('#modalOfficialTitle').textContent = 'Edit Official';
      $('#offName').value = off.full_name;
      $('#offEmail').value = off.email;
      $('#offRole').value = off.role_title;
      const permInput = document.querySelector(`[name="perm"][value="${off.permission_level}"]`);
      if (permInput) permInput.checked = true;
    } else {
      editingOfficialId = null;
      $('#modalOfficialTitle').textContent = 'Add Official';
      $('#officialForm').reset();
      const def = document.querySelector('[name="perm"][value="Coordinator"]');
      if (def) def.checked = true;
    }
    openModal('modalOfficial');
  }

  $('#openAddOfficial').addEventListener('click', () => openOfficialModal(null));

  $('#officialsGrid').addEventListener('click', e => {
    const editBtn = e.target.closest('[data-off-edit]');
    const delBtn = e.target.closest('[data-off-delete]');
    if (editBtn) {
      const id = parseInt(editBtn.dataset.offEdit, 10);
      openOfficialModal(OFFICIALS.find(o => o.id === id));
    } else if (delBtn) {
      const id = parseInt(delBtn.dataset.offDelete, 10);
      const off = OFFICIALS.find(o => o.id === id);
      if (!off) return;
      pendingDeleteId = id;
      pendingDeleteType = 'official';
      $('#deleteTitle').textContent = `Remove "${off.full_name}"?`;
      openModal('modalDelete');
    }
  });

  $('#saveOfficial').addEventListener('click', async () => {
    const name = $('#offName').value.trim();
    if (!name) { alert('Please enter a name.'); return; }
    const email = $('#offEmail').value.trim();
    if (!email) { alert('Please enter an email.'); return; }

    const fd = new FormData();
    fd.append('full_name', name);
    fd.append('email', email);
    fd.append('role_title', $('#offRole').value.trim());
    const perm = document.querySelector('[name="perm"]:checked');
    fd.append('permission_level', perm ? perm.value : 'Coordinator');
    const photo = document.querySelector('#officialForm input[type=file]');
    if (photo && photo.files[0]) fd.append('photo', photo.files[0]);

    const url = editingOfficialId ? `/api/officials/${editingOfficialId}/` : '/api/officials/';
    const btn = $('#saveOfficial');
    btn.disabled = true;
    btn.textContent = 'Saving…';
    try {
      const res = await apiFetch(url, { method: 'POST', body: fd });
      if (res.ok) {
        closeModal('modalOfficial');
        await loadOfficials();
        populateAssignSelect();
      } else {
        const d = await res.json();
        alert('Error: ' + (d.error || 'Could not save official.'));
      }
    } finally {
      btn.disabled = false;
      btn.textContent = 'Save Official';
    }
  });

  /* =====================================================
     MEMBERS
  ===================================================== */
  async function loadMembers() {
    try {
      const res = await apiFetch('/api/members/');
      if (!res.ok) return;
      MEMBERS = await res.json();
      renderMembers();
    } catch (e) { /* silent */ }
  }

  function renderMembers() {
    const tbody = $('#membersBody');
    const meta = $('#membersMeta');
    if (!MEMBERS.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:#9a8a9c;">
        No members yet. Click <strong>Add Member</strong> to register the first member.
      </td></tr>`;
      if (meta) meta.textContent = '0 members';
      return;
    }
    if (meta) meta.textContent = `${MEMBERS.length} member${MEMBERS.length === 1 ? '' : 's'}`;
    tbody.innerHTML = MEMBERS.map(m => `
      <tr data-id="${m.id}">
        <td>
          <div class="row-title">
            ${avatarHTML(m.initials, 'sm', m.full_name)}
            <div class="row-title__main" style="margin-left:10px">
              <strong>${escHtml(m.full_name)}</strong>
            </div>
          </div>
        </td>
        <td>${escHtml(m.email)}</td>
        <td>${escHtml(m.student_id) || '—'}</td>
        <td>${escHtml(m.course)}</td>
        <td>Year ${m.year_of_study}</td>
        <td><span class="status status--${m.is_active ? 'upcoming' : 'past'}">${m.is_active ? 'Active' : 'Inactive'}</span></td>
        <td>
          <div class="actions">
            <button class="action-btn" data-mem-edit="${m.id}" title="Edit">${ICONS.pencil}</button>
            <button class="action-btn action-btn--danger" data-mem-delete="${m.id}" title="Delete">${ICONS.trash}</button>
          </div>
        </td>
      </tr>`).join('');
  }

  /* ---------- Member Modal ---------- */
  let editingMemberId = null;

  function openMemberModal(mem) {
    if (mem) {
      editingMemberId = mem.id;
      $('#modalMemberTitle').textContent = 'Edit Member';
      $('#memName').value = mem.full_name;
      $('#memEmail').value = mem.email;
      $('#memStudentId').value = mem.student_id || '';
      $('#memCourse').value = mem.course;
      $('#memYear').value = mem.year_of_study;
    } else {
      editingMemberId = null;
      $('#modalMemberTitle').textContent = 'Add Member';
      $('#memberForm').reset();
    }
    openModal('modalMember');
  }

  $('#openAddMember').addEventListener('click', () => openMemberModal(null));

  $('#membersBody').addEventListener('click', e => {
    const editBtn = e.target.closest('[data-mem-edit]');
    const delBtn = e.target.closest('[data-mem-delete]');
    if (editBtn) {
      const m = MEMBERS.find(x => x.id === parseInt(editBtn.dataset.memEdit, 10));
      if (m) openMemberModal(m);
    } else if (delBtn) {
      const id = parseInt(delBtn.dataset.memDelete, 10);
      const m = MEMBERS.find(x => x.id === id);
      if (!m) return;
      pendingDeleteId = id;
      pendingDeleteType = 'member';
      $('#deleteTitle').textContent = `Remove member "${m.full_name}"?`;
      openModal('modalDelete');
    }
  });

  $('#saveMember').addEventListener('click', async () => {
    const name = $('#memName').value.trim();
    const email = $('#memEmail').value.trim();
    if (!name || !email) { alert('Name and email are required.'); return; }

    const payload = {
      full_name: name,
      email,
      student_id: $('#memStudentId').value.trim(),
      course: $('#memCourse').value.trim(),
      year_of_study: parseInt($('#memYear').value, 10),
    };
    if (editingMemberId) payload.is_active = true;

    const url = editingMemberId ? `/api/members/${editingMemberId}/` : '/api/members/';
    const btn = $('#saveMember');
    btn.disabled = true; btn.textContent = 'Saving…';
    try {
      const res = await apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        closeModal('modalMember');
        await Promise.all([loadMembers(), loadStats()]);
      } else {
        const d = await res.json();
        alert('Error: ' + (d.error || 'Could not save member.'));
      }
    } finally {
      btn.disabled = false; btn.textContent = 'Save Member';
    }
  });

  /* =====================================================
     GALLERY
  ===================================================== */
  async function loadGallery() {
    try {
      const res = await apiFetch('/api/gallery/');
      if (!res.ok) return;
      GALLERY = await res.json();
      renderGallery();
    } catch (e) { /* silent */ }
  }

  function renderGallery() {
    const grid = $('#galleryGrid');
    if (!GALLERY.length) {
      grid.innerHTML = `<div class="empty-card" style="grid-column:1/-1">
        <h3>No photos yet</h3>
        <p>Click <strong>Add Photo</strong> to upload the first gallery item.</p>
      </div>`;
      return;
    }
    grid.innerHTML = GALLERY.map(g => `
      <article class="off-card" data-id="${g.id}">
        <div style="width:100%;height:120px;background:#f3eff4;border-radius:8px;overflow:hidden;margin-bottom:12px;display:flex;align-items:center;justify-content:center;">
          ${g.image
            ? `<img src="${g.image}" style="width:100%;height:100%;object-fit:cover;" alt="${escHtml(g.title)}" />`
            : ICONS.image}
        </div>
        <div class="off-card__id">
          <strong>${escHtml(g.title)}</strong>
          <span>${escHtml(g.category)}${g.event_date ? ' · ' + fmtDateTime(g.event_date) : ''}</span>
        </div>
        ${({ header: '📸 Header Photo', looking_back: '⏪ Looking Back', partners: '🤝 Partners' }[g.photo_type] || g.photo_type)
          ? `<span class="off-card__perm">${{ header: '📸 Header Photo', looking_back: '⏪ Looking Back', partners: '🤝 Partners' }[g.photo_type] || g.photo_type}</span>`
          : ''}
        <div class="off-card__actions">
          <button class="btn btn--ghost" data-gal-edit="${g.id}">Edit</button>
          <button class="btn btn--ghost btn--danger-outline" data-gal-delete="${g.id}">Remove</button>
        </div>
      </article>`).join('');
  }

  /* ---------- Gallery Modal ---------- */
  const PHOTO_TYPE_HINTS = {
    header:       'Only the first Header Photo is shown as the hero image on the landing page.',
    looking_back: 'Shown in the "Looking Back" slideshow, ordered most recent first.',
    partners:     'Shown in the Partners ticker. Paste the partner\'s website URL in the Description field below.',
  };

  function updateGalleryTypeHint() {
    const type = $('#galPhotoType') ? $('#galPhotoType').value : '';
    const hint = document.getElementById('galPhotoTypeHint');
    const descLabel = document.getElementById('galDescLabel');
    if (hint) hint.textContent = PHOTO_TYPE_HINTS[type] || '';
    if (descLabel) descLabel.textContent = type === 'partners' ? 'Website URL' : 'Description';
    const descEl = document.getElementById('galDesc');
    if (descEl) descEl.placeholder = type === 'partners'
      ? 'https://partnerwebsite.com'
      : 'Short caption for this photo or event.';
  }

  let editingGalleryId = null;

  function openGalleryModal(item) {
    if (item) {
      editingGalleryId = item.id;
      $('#modalGalleryTitle').textContent = 'Edit Photo';
      $('#galTitle').value = item.title;
      $('#galCategory').value = item.category;
      $('#galDate').value = item.event_date || '';
      $('#galDesc').value = item.description || '';
      $('#galPhotoType').value = item.photo_type || 'looking_back';
      $('#galOrder').value = item.display_order ?? 0;
    } else {
      editingGalleryId = null;
      $('#modalGalleryTitle').textContent = 'Add Photo';
      $('#galleryForm').reset();
      $('#galPhotoType').value = 'looking_back';
      $('#galOrder').value = 0;
    }
    updateGalleryTypeHint();
    openModal('modalGallery');
  }

  $('#openAddGallery').addEventListener('click', () => openGalleryModal(null));
  document.getElementById('galPhotoType') && document.getElementById('galPhotoType').addEventListener('change', updateGalleryTypeHint);

  $('#galleryGrid').addEventListener('click', e => {
    const editBtn = e.target.closest('[data-gal-edit]');
    const delBtn = e.target.closest('[data-gal-delete]');
    if (editBtn) {
      const g = GALLERY.find(x => x.id === parseInt(editBtn.dataset.galEdit, 10));
      if (g) openGalleryModal(g);
    } else if (delBtn) {
      const id = parseInt(delBtn.dataset.galDelete, 10);
      const g = GALLERY.find(x => x.id === id);
      if (!g) return;
      pendingDeleteId = id;
      pendingDeleteType = 'gallery';
      $('#deleteTitle').textContent = `Remove photo "${g.title}"?`;
      openModal('modalDelete');
    }
  });

  $('#saveGallery').addEventListener('click', async () => {
    const title = $('#galTitle').value.trim();
    if (!title) { alert('Please enter a title.'); return; }

    const fd = new FormData();
    fd.append('title', title);
    fd.append('category', $('#galCategory').value);
    fd.append('event_date', $('#galDate').value);
    fd.append('description', $('#galDesc').value.trim());
    fd.append('photo_type', $('#galPhotoType').value);
    fd.append('display_order', $('#galOrder').value || '0');
    const imgFile = $('#dropzoneGallery input[type=file]').files[0];
    if (imgFile) fd.append('image', imgFile);

    const url = editingGalleryId ? `/api/gallery/${editingGalleryId}/` : '/api/gallery/';
    const btn = $('#saveGallery');
    btn.disabled = true; btn.textContent = 'Saving…';
    try {
      const res = await apiFetch(url, { method: 'POST', body: fd });
      if (res.ok) {
        closeModal('modalGallery');
        await loadGallery();
      } else {
        const d = await res.json();
        alert('Error: ' + (d.error || 'Could not save.'));
      }
    } finally {
      btn.disabled = false; btn.textContent = 'Save Photo';
    }
  });

  /* =====================================================
     ANNOUNCEMENTS
  ===================================================== */
  async function loadAnnouncements() {
    try {
      const res = await apiFetch('/api/announcements/');
      if (!res.ok) return;
      ANNOUNCEMENTS = await res.json();
      renderAnnouncements();
    } catch (e) { /* silent */ }
  }

  function renderAnnouncements() {
    const tbody = $('#announcementsBody');
    if (!ANNOUNCEMENTS.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;padding:32px;color:#9a8a9c;">
        No announcements yet. Click <strong>New Announcement</strong> to create one.
      </td></tr>`;
      return;
    }
    tbody.innerHTML = ANNOUNCEMENTS.map(a => `
      <tr data-id="${a.id}">
        <td>
          <strong>${escHtml(a.title)}</strong>
          <span class="badge badge--gold" style="margin-left:8px;font-size:10px;padding:3px 8px;">${escHtml(a.category || 'General')}</span>
        </td>
        <td><span class="status status--${a.is_published ? 'upcoming' : 'past'}">${a.is_published ? 'Published' : 'Draft'}</span></td>
        <td>${fmtDateTime(a.created_at)}</td>
        <td>
          <div class="actions">
            <button class="action-btn" data-ann-edit="${a.id}" title="Edit">${ICONS.pencil}</button>
            <button class="action-btn action-btn--danger" data-ann-delete="${a.id}" title="Delete">${ICONS.trash}</button>
          </div>
        </td>
      </tr>`).join('');
  }

  /* ---------- Announcement Modal ---------- */
  let editingAnnouncementId = null;

  function openAnnouncementModal(ann) {
    if (ann) {
      editingAnnouncementId = ann.id;
      $('#modalAnnouncementTitle').textContent = 'Edit Announcement';
      $('#annTitle').value = ann.title;
      $('#annBody').value = ann.body;
      $('#annCategory').value = ann.category || 'General';
    } else {
      editingAnnouncementId = null;
      $('#modalAnnouncementTitle').textContent = 'New Announcement';
      $('#announcementForm').reset();
      $('#annCategory').value = 'General';
    }
    const btn = $('#saveAnnouncement');
    if (btn) btn.textContent = editingAnnouncementId ? 'Update Announcement' : 'Publish Announcement';
    openModal('modalAnnouncement');
  }

  $('#openAddAnnouncement').addEventListener('click', () => openAnnouncementModal(null));

  $('#announcementsBody').addEventListener('click', e => {
    const editBtn = e.target.closest('[data-ann-edit]');
    const delBtn = e.target.closest('[data-ann-delete]');
    if (editBtn) {
      const a = ANNOUNCEMENTS.find(x => x.id === parseInt(editBtn.dataset.annEdit, 10));
      if (a) openAnnouncementModal(a);
    } else if (delBtn) {
      const id = parseInt(delBtn.dataset.annDelete, 10);
      const a = ANNOUNCEMENTS.find(x => x.id === id);
      if (!a) return;
      pendingDeleteId = id;
      pendingDeleteType = 'announcement';
      $('#deleteTitle').textContent = `Delete announcement "${a.title}"?`;
      openModal('modalDelete');
    }
  });

  $('#saveAnnouncement').addEventListener('click', async () => {
    const title = $('#annTitle').value.trim();
    const body = $('#annBody').value.trim();
    if (!title || !body) { alert('Title and body are required.'); return; }

    const isNew = !editingAnnouncementId;
    const payload = {
      title,
      body,
      category: $('#annCategory').value,
      is_published: true,
    };

    const url = editingAnnouncementId ? `/api/announcements/${editingAnnouncementId}/` : '/api/announcements/';
    const btn = $('#saveAnnouncement');
    const originalLabel = btn.textContent;
    btn.disabled = true; btn.textContent = isNew ? 'Publishing…' : 'Updating…';
    try {
      const res = await apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        closeModal('modalAnnouncement');
        await loadAnnouncements();
      } else {
        const d = await res.json();
        alert('Error: ' + (d.error || 'Could not save.'));
      }
    } finally {
      btn.disabled = false; btn.textContent = originalLabel;
    }
  });

  /* =====================================================
     DELETE (shared confirm modal)
  ===================================================== */
  $('#confirmDelete').addEventListener('click', async () => {
    if (pendingDeleteId == null) { closeModal('modalDelete'); return; }

    const urlMap = {
      event: `/api/events/${pendingDeleteId}/`,
      official: `/api/officials/${pendingDeleteId}/`,
      member: `/api/members/${pendingDeleteId}/`,
      gallery: `/api/gallery/${pendingDeleteId}/`,
      announcement: `/api/announcements/${pendingDeleteId}/`,
    };

    const url = urlMap[pendingDeleteType];
    if (!url) { closeModal('modalDelete'); return; }

    try {
      const res = await apiFetch(url, { method: 'DELETE' });
      if (res.ok) {
        closeModal('modalDelete');
        if (pendingDeleteType === 'event')        { await Promise.all([loadEvents(), loadStats()]); }
        if (pendingDeleteType === 'official')     { await loadOfficials(); }
        if (pendingDeleteType === 'member')       { await Promise.all([loadMembers(), loadStats()]); }
        if (pendingDeleteType === 'gallery')      { await loadGallery(); }
        if (pendingDeleteType === 'announcement') { await loadAnnouncements(); }
      }
    } catch (e) { /* silent */ }
    pendingDeleteId = null;
    pendingDeleteType = null;
  });

  /* =====================================================
     VIEW SWITCHING
  ===================================================== */
  const VIEW_META = {
    dashboard:     { title: 'Dashboard',            sub: 'Overview of the chapter at a glance.' },
    events:        { title: 'Events Management',    sub: 'Create, schedule, and assign officials to chapter events.' },
    officials:     { title: 'Officials & Roles',    sub: 'Manage chapter committee profiles and permissions.' },
    members:       { title: 'Members',              sub: 'Chapter membership directory.' },
    gallery:       { title: 'Gallery',              sub: 'Past event photography and media.' },
    announcements: { title: 'Announcements',        sub: 'Chapter-wide announcements and notices.' },
    settings:      { title: 'Settings',             sub: 'Configuration, integrations, and admin permissions.' },
  };

  function setView(view) {
    $$('.nav-item').forEach(n => n.classList.toggle('is-active', n.dataset.view === view));
    $$('.view').forEach(v => v.classList.toggle('is-active', v.dataset.view === view));
    const meta = VIEW_META[view];
    if (meta) {
      $('#pageTitle').textContent = meta.title;
      $('#pageSub').textContent = meta.sub;
    }
    $('#sidebar').classList.remove('is-open');
  }

  $$('.nav-item[data-view]').forEach(item => {
    item.addEventListener('click', e => { e.preventDefault(); setView(item.dataset.view); });
  });
  $$('[data-jump]').forEach(b => b.addEventListener('click', () => setView(b.dataset.jump)));

  /* =====================================================
     MODAL HELPERS
  ===================================================== */
  function openModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.hidden = false;
    document.body.style.overflow = 'hidden';
  }
  function closeModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.hidden = true;
    document.body.style.overflow = '';
  }

  document.addEventListener('click', e => {
    const t = e.target.closest('[data-close]');
    if (t) { const m = t.closest('.modal'); if (m) closeModal(m.id); }
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      $$('.modal').forEach(m => { if (!m.hidden) closeModal(m.id); });
      closePanel();
    }
  });

  /* ---------- Toggle groups ---------- */
  function setToggle(name, val) {
    const group = document.querySelector(`.toggle-group[data-toggle="${name}"]`);
    if (!group) return;
    group.querySelectorAll('.toggle-opt').forEach(b => {
      b.classList.toggle('is-active', b.dataset.val === val);
    });
  }

  $$('.toggle-group').forEach(g => {
    g.addEventListener('click', e => {
      const btn = e.target.closest('.toggle-opt');
      if (!btn) return;
      g.querySelectorAll('.toggle-opt').forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');
    });
  });

  /* =====================================================
     DROPZONES
  ===================================================== */
  function setupDropzone(zone) {
    if (!zone) return;
    const input = zone.querySelector('input[type=file]');
    const preview = zone.querySelector('.dropzone__preview');
    function handle(file) {
      if (!file || !file.type.startsWith('image/')) return;
      const reader = new FileReader();
      reader.onload = e => {
        if (preview) preview.style.backgroundImage = `url(${e.target.result})`;
        zone.classList.add('has-file');
      };
      reader.readAsDataURL(file);
    }
    input.addEventListener('change', e => handle(e.target.files[0]));
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.style.borderColor = 'var(--purple)'; });
    zone.addEventListener('dragleave', () => { zone.style.borderColor = ''; });
    zone.addEventListener('drop', e => { e.preventDefault(); zone.style.borderColor = ''; handle(e.dataTransfer.files[0]); });
  }
  $$('.dropzone').forEach(setupDropzone);

  /* =====================================================
     NOTIFICATIONS PANEL
  ===================================================== */
  const panel = $('#notifPanel');
  const panelBackdrop = $('#panelBackdrop');

  function openPanel() {
    panel.classList.add('is-open');
    panel.setAttribute('aria-hidden', 'false');
    panelBackdrop.classList.add('is-open');
  }
  function closePanel() {
    panel.classList.remove('is-open');
    panel.setAttribute('aria-hidden', 'true');
    panelBackdrop.classList.remove('is-open');
  }
  $('#bellBtn').addEventListener('click', openPanel);
  $('#closePanel').addEventListener('click', closePanel);
  panelBackdrop.addEventListener('click', closePanel);
  $('#notifList').innerHTML = '<li style="padding:24px;text-align:center;color:#9a8a9c;font-size:13px;">No notifications</li>';

  /* =====================================================
     MOBILE SIDEBAR
  ===================================================== */
  $('#menuToggle').addEventListener('click', () => $('#sidebar').classList.add('is-open'));
  $('#sidebarClose').addEventListener('click', () => $('#sidebar').classList.remove('is-open'));

  /* =====================================================
     PROFILE DROPDOWN
  ===================================================== */
  const profileBtn = $('#profileBtn');
  const profileDropdown = $('#profileDropdown');
  profileBtn.addEventListener('click', e => { e.stopPropagation(); profileDropdown.classList.toggle('is-open'); });
  document.addEventListener('click', () => profileDropdown.classList.remove('is-open'));

  /* =====================================================
     SECURITY: XSS escape
  ===================================================== */
  function escHtml(str) {
    if (str == null) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  /* =====================================================
     INIT — load everything
  ===================================================== */
  async function init() {
    await Promise.all([
      loadStats(),
      loadOfficials(),
      loadEvents(),
      loadMembers(),
      loadGallery(),
      loadAnnouncements(),
    ]);
  }

  init();

})();
