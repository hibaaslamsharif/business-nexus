const API_BASE = '';

// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

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
      console.log('Sending registration request to:', '/auth/register/');
      console.log('Payload:', payload);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const res = await fetch('/auth/register/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload),
        credentials: 'same-origin'
      });
      
      clearTimeout(timeoutId);
      console.log('Response status:', res.status);
      console.log('Response ok:', res.ok);
      
      if (!res.ok) {
        const errorText = await res.text();
        console.log('Error response:', errorText);
        throw new Error(`HTTP ${res.status}: ${errorText}`);
      }
      
      const data = await res.json();
      console.log('Response data:', data);
      
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
      console.error('Registration error:', err);
      if (err.name === 'AbortError') {
        alert('Registration timed out. Please try again.');
      } else if (err.message.includes('Failed to fetch')) {
        alert('Network error. Please check if the server is running and try again.');
      } else {
        alert('Registration failed: ' + err.message);
      }
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


