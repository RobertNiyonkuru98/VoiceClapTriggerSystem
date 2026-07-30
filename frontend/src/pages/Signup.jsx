import { useState } from 'react';
import axios from 'axios';
import { UserPlus, Siren } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '', role: 'health_responder' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await axios.post('/api/auth/signup/responder', form);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container flex-center" style={{ minHeight: '80vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <Siren size={36} color="var(--brand-color)" style={{ marginBottom: '0.25rem' }} />
          <div><span className="brand-font">MTEAS</span></div>
        </div>
        <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Responder Signup</h2>
        
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
          
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Role</label>
            <select 
              className="input-field" 
              value={form.role}
              onChange={e => setForm({...form, role: e.target.value})}
            >
              <option value="health_responder">Healthcare Responder</option>
              <option value="fire_responder">Fire Responder</option>
              <option value="police_responder">Police / Danger Responder</option>
              <option value="admin">System Administrator</option>
            </select>
          </div>
          
          <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: '1rem' }}>
            <UserPlus size={18}/> {loading ? 'Creating...' : 'Create Account'}
          </button>
        </form>
        
        <div style={{ marginTop: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Registering a household IoT device? <br/>
          <a href="/signup/household" style={{ color: 'var(--brand-color)' }}>Device Registration Form</a>
        </div>
      </div>
    </div>
  );
}
