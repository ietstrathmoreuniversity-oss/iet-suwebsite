/* IET Strathmore — interactivity */
(function(){
  'use strict';

  /* ---------- Scroll reveal ---------- */
  const revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window){
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting){
          e.target.classList.add('is-visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(el => io.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('is-visible'));
  }

  /* ---------- Nav: mobile toggle ---------- */
  const toggle = document.querySelector('.nav__toggle');
  const nav = document.querySelector('.nav');
  if (toggle){
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }

  /* ---------- Voices: simple mobile dot indicator ---------- */
  const grid = document.getElementById('voicesGrid');
  const dots = document.getElementById('voicesDots');
  if (grid && dots){
    const items = grid.children;
    for (let i = 0; i < items.length; i++){
      const s = document.createElement('span');
      if (i === 0) s.classList.add('is-active');
      dots.appendChild(s);
    }
    grid.addEventListener('scroll', () => {
      const idx = Math.round(grid.scrollLeft / grid.clientWidth);
      [...dots.children].forEach((d, i) => d.classList.toggle('is-active', i === idx));
    }, { passive: true });
  }

  /* ---------- Tweaks panel (vanilla, no external host required) ---------- */
  const DEFAULTS = /*EDITMODE-BEGIN*/{
    "pattern": "circuit",
    "eventsTheme": "dark",
    "displayFont": "Poppins",
    "animatedCtas": true
  }/*EDITMODE-END*/;

  function applyTweaks(state){
    document.body.dataset.pattern = state.pattern;
    document.body.dataset.events  = state.eventsTheme;
    document.body.dataset.display = state.displayFont;
    document.body.classList.toggle('animated-ctas', !!state.animatedCtas);
  }

  const state = { ...DEFAULTS };
  applyTweaks(state);

  const panel  = document.getElementById('tweaks');
  const closer = panel ? panel.querySelector('.tweaks__close') : null;

  function setPanelVisible(v){
    if (!panel) return;
    panel.hidden = !v;
  }

  // Initialize controls
  if (panel){
    panel.querySelectorAll('[data-tweak]').forEach(ctrl => {
      const key = ctrl.dataset.tweak;
      if (ctrl.type === 'checkbox') ctrl.checked = !!state[key];
      else ctrl.value = state[key];

      ctrl.addEventListener('change', () => {
        const val = ctrl.type === 'checkbox' ? ctrl.checked : ctrl.value;
        state[key] = val;
        applyTweaks(state);
        try {
          window.parent && window.parent.postMessage({
            type: '__edit_mode_set_keys',
            edits: { [key]: val }
          }, '*');
        } catch (e){}
      });
    });

    if (closer){
      closer.addEventListener('click', () => {
        setPanelVisible(false);
        try { window.parent.postMessage({ type: '__edit_mode_dismissed' }, '*'); } catch(e){}
      });
    }
  }

  /* ---------- Infinite-scroll carousels (Looking Back + Partners) ---------- */
  function initInfiniteTrack(id) {
    const track = document.getElementById(id);
    if (!track || !track.children.length) return;
    const origItems = [...track.children];
    // Pad with extra clones until we fill at least one viewport width
    while (track.scrollWidth < window.innerWidth) {
      origItems.forEach(child => track.appendChild(child.cloneNode(true)));
    }
    // Duplicate the full current set once — CSS then animates translateX(-50%) for a seamless loop
    [...track.children].forEach(child => track.appendChild(child.cloneNode(true)));
  }
  initInfiniteTrack('lbTrack');
  initInfiniteTrack('partnerTicker');

  // Host protocol: register listener FIRST, then announce.
  window.addEventListener('message', (e) => {
    const t = e && e.data && e.data.type;
    if (t === '__activate_edit_mode')   setPanelVisible(true);
    if (t === '__deactivate_edit_mode') setPanelVisible(false);
  });
  try { window.parent.postMessage({ type: '__edit_mode_available' }, '*'); } catch(e){}

})();
