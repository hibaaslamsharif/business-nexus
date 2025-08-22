const API_BASE = (() => {
  const host = window.location.hostname || '127.0.0.1';
  const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
  const port = '8000';
  return `${protocol}://${host}:${port}`;
})();

// Register
const registerForm = document.getElementById('registerForm');
if (registerForm) {
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      username: document.getElementById('username').value,
      email: document.getElementById('email').value,
      password: document.getElementById('password').value,
      role: document.getElementById('role').value,
    };
    try {
      const res = await fetch(`${API_BASE}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registration failed');
      localStorage.setItem('token', data.access);
      localStorage.setItem('role', data.role);
      localStorage.setItem('username', data.username || payload.username);
      alert('Registration successful! Redirecting to dashboard...');
      if (data.role === 'investor') {
        window.location.href = '/dashboard_investor/';
      } else {
        window.location.href = '/dashboard_entrepreneur/';
      }
    } catch (err) {
      alert(err.message);
    }
  });
}

// Login
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      email: document.getElementById('email').value,
      password: document.getElementById('password').value,
    };
    try {
      const res = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      localStorage.setItem('token', data.access);
      localStorage.setItem('role', data.role);
      localStorage.setItem('username', data.username || '');
      if (data.role === 'investor') {
        window.location.href = '/dashboard_investor/';
      } else {
        window.location.href = '/dashboard_entrepreneur/';
      }
    } catch (err) {
      alert(err.message);
    }
  });
}


