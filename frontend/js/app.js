const API = {
  base: (() => {
  const { protocol, hostname, port } = window.location;
  const proto = protocol === 'https:' ? 'https' : 'http';
  // Use current port if available, else default to 8000
  const effectivePort = port && port.length ? port : '8000';
  return `${proto}://${hostname}${effectivePort ? `:${effectivePort}` : ''}`;
  })(),
  token() { return localStorage.getItem('token') || ''; },
  headers(json = true) {
    const h = {};
    if (json) h['Content-Type'] = 'application/json';
    const t = this.token();
    if (t) h['Authorization'] = `Bearer ${t}`;
    return h;
  },
  async get(path) {
    const res = await fetch(`${this.base}${path}`, { headers: this.headers(false) });
    if (!res.ok) throw new Error((await res.json()).detail || 'Request failed');
    return res.json();
  },
  async post(path, body) {
    const res = await fetch(`${this.base}${path}`, { method: 'POST', headers: this.headers(), body: JSON.stringify(body) });
    if (!res.ok) throw new Error((await res.json()).detail || 'Request failed');
    return res.json();
  },
  async put(path, body) {
    const res = await fetch(`${this.base}${path}`, { method: 'PUT', headers: this.headers(), body: JSON.stringify(body) });
    if (!res.ok) throw new Error((await res.json()).detail || 'Request failed');
    return res.json();
  },
  async patch(path, body) {
    const res = await fetch(`${this.base}${path}`, { method: 'PATCH', headers: this.headers(), body: JSON.stringify(body) });
    if (!res.ok) throw new Error((await res.json()).detail || 'Request failed');
    return res.json();
  }
};

function requireAuth(role) {
  const token = localStorage.getItem('token');
  const userRole = localStorage.getItem('role');
  if (!token) { window.location.href = '/login/'; return false; }
  if (role && userRole !== role) { window.location.href = '/'; return false; }
  return true;
}

function el(tag, attrs = {}, children = []) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'class') e.className = v; else if (k.startsWith('on') && typeof v === 'function') e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
  });
  children.forEach(c => e.append(c));
  return e;
}

async function loadEntrepreneurs() {
  if (!requireAuth('investor')) return;
  const container = document.getElementById('list');
  container.innerHTML = 'Loading...';
  try {
    const data = await API.get('/api/entrepreneurs/');
    container.innerHTML = '';
    data.forEach(p => {
      const card = el('div', { class: 'card' }, [
        el('h3', {}, [p.user.username]),
        el('p', {}, [p.startup_name || '—']),
        el('p', {}, [p.startup_description || '—']),
        el('div', { class: 'actions' }, [
          el('a', { class: 'button secondary', href: `/profile/${p.user.id}/` }, ['View Profile']),
          el('button', { class: 'button', onclick: async () => {
            try { await API.post('/api/request/', { entrepreneur_id: p.user.id, message: 'Interested in collaborating.' }); alert('Request sent'); }
            catch (e) { alert(e.message); }
          } }, ['Send Request'])
        ])
      ]);
      container.append(card);
    });
  } catch (e) {
    container.innerHTML = '';
    container.append(el('div', { class: 'card' }, [e.message]));
  }
}

async function loadRequests() {
  if (!requireAuth('entrepreneur')) return;
  const container = document.getElementById('requests');
  container.innerHTML = 'Loading...';
  try {
    const data = await API.get('/api/requests/');
    container.innerHTML = '';
    data.forEach(r => {
      const badgeClass = r.status === 'Accepted' ? 'badge-accepted' : r.status === 'Rejected' ? 'badge-rejected' : 'badge-pending';
      const actions = [];
      if (r.status === 'Pending') {
        actions.push(el('button', { class: 'button', onclick: async () => { await API.patch(`/api/request/${r.id}/`, { status: 'Accepted' }); alert('Accepted'); loadRequests(); } }, ['Accept']));
        actions.push(el('button', { class: 'button secondary', onclick: async () => { await API.patch(`/api/request/${r.id}/`, { status: 'Rejected' }); alert('Rejected'); loadRequests(); } }, ['Reject']));
      }
      const row = el('div', { class: 'card' }, [
        el('div', {}, [`From: ${r.investor.username}`]),
        el('div', {}, [r.message || '—']),
        el('div', { class: `badge ${badgeClass}` }, [r.status]),
        el('div', { class: 'actions' }, actions)
      ]);
      container.append(row);
    });
  } catch (e) {
    container.innerHTML = '';
    container.append(el('div', { class: 'card' }, [e.message]));
  }
}

async function loadProfile(userId) {
  const container = document.getElementById('profile');
  container.innerHTML = 'Loading...';
  try {
    const data = await API.get(`/api/profile/${userId}/`);
    container.innerHTML = '';
    const items = [
      ['Username', data.user.username],
      ['Role', data.user.role],
      ['Bio', data.bio || '—'],
  ['Profile Views', String(data.view_count || 0)],
    ];
    if (data.user.role === 'entrepreneur') {
      items.push(['Startup', data.startup_name || '—']);
      items.push(['Description', data.startup_description || '—']);
      items.push(['Funding Need', data.funding_need || '—']);
      items.push(['Pitch Deck', data.pitch_deck_url ? data.pitch_deck_url : '—']);
    } else {
      items.push(['Interests', data.investment_interests || '—']);
      items.push(['Portfolio', data.portfolio_companies || '—']);
    }
    items.forEach(([k, v]) => container.append(el('div', { class: 'card' }, [el('strong', {}, [`${k}: `]), v])));
    // Recent viewers list (if you are viewing your own profile, helpful to see who viewed)
    if (Array.isArray(data.recent_viewers) && data.recent_viewers.length) {
      const list = el('div', { class: 'card' }, [
        el('h4', {}, ['Recent Viewers']),
        ...data.recent_viewers.map(v => el('div', {}, [
          `${v.username} — ${new Date(v.viewed_at).toLocaleString()}`
        ]))
      ]);
      container.append(list);
    }
  } catch (e) {
    container.innerHTML = '';
    container.append(el('div', { class: 'card' }, [e.message]));
  }
}

async function initEditProfile() {
  if (!requireAuth()) return;
  const form = document.getElementById('editProfileForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      await API.put('/api/profile/', payload);
      alert('Profile updated');
    } catch (err) {
      alert(err.message);
    }
  });
}

async function loadMyRequests() {
  if (!requireAuth('investor')) return;
  const container = document.getElementById('myRequests');
  if (!container) return;
  container.innerHTML = 'Loading...';
  try {
    const data = await API.get('/api/requests/');
    container.innerHTML = '';
    data.forEach(r => {
      const badgeClass = r.status === 'Accepted' ? 'badge-accepted' : r.status === 'Rejected' ? 'badge-rejected' : 'badge-pending';
      const row = el('div', { class: 'card' }, [
        el('div', {}, [`To: ${r.entrepreneur.username}`]),
        el('div', {}, [r.message || '—']),
        el('div', { class: `badge ${badgeClass}` }, [r.status]),
      ]);
      container.append(row);
    });
  } catch (e) {
    container.innerHTML = '';
    container.append(el('div', { class: 'card' }, [e.message]));
  }
}

window.Dashboard = { loadEntrepreneurs, loadRequests, loadMyRequests, loadProfile, initEditProfile };

