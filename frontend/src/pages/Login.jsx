import { useState } from 'react';
import axios from 'axios';
import { LogIn, Siren } from 'lucide-react';

export default function Login({ setUser }) {
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', form.username);
      formData.append('password', form.password);
      
      const res = await axios.post('/api/auth/login', formData);
      localStorage.setItem('token', res.data.access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`;
      
      setUser(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container flex-center" style={{ minHeight: '80vh', flexDirection: 'column', gap: 0 }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <Siren size={36} color="var(--brand-color)" style={{ marginBottom: '0.25rem' }} />
          <div><span className="brand-font">MTEAS</span></div>
        </div>
        <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Responder / Admin Login</h2>
        
        {error && <div className="alert-card alert-fire" style={{ padding: '1rem', marginBottom: '1rem', background: 'rgba(239, 68, 68, 0.1)' }}>{error}</div>}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Username</label>
            <input 
              type="text" 
              className="input-field" 
              required
              value={form.username}
              onChange={e => setForm({...form, username: e.target.value})}
            />
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Password</label>
            <input 
              type="password" 
              className="input-field" 
              required
              value={form.password}
              onChange={e => setForm({...form, password: e.target.value})}
            />
          </div>
          
          <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: '1rem' }}>
            <LogIn size={18}/> {loading ? 'Logging in...' : 'Sign In'}
          </button>
        </form>
        
        <div style={{ marginTop: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Need an account? <a href="/signup" style={{ color: 'var(--brand-color)' }}>Sign up here</a>
        </div>
      </div>
      <div style={{ marginTop: '1.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', opacity: 0.55, textAlign: 'center' }}>
        © 2026 Tony Robert · MTEAS
      </div>
    </div>
  );
}
