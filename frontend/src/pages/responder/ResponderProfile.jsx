import { useState } from 'react';
import { User, Shield, Briefcase, Mail } from 'lucide-react';

const ROLE_LABELS = {
  health_responder: 'Medical Services',
  fire_responder:   'Fire Department',
  police_responder: 'Police / Security',
};

export default function ResponderProfile({ user }) {
  const [onDuty, setOnDuty] = useState(true);

  return (
    <div className="animate-slide-in">
      <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2rem' }}>
        <User size={24} /> Responder Profile
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        
        {/* Profile Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <div style={{ 
            width: 80, height: 80, borderRadius: '50%', background: 'var(--brand-color)', 
            display: 'flex', alignItems: 'center', justifyContent: 'center', 
            fontSize: '2rem', fontWeight: 700, color: '#111827', marginBottom: '1rem' 
          }}>
            {user.username.charAt(0).toUpperCase()}
          </div>
          <h2 style={{ marginBottom: '0.25rem' }}>{user.username}</h2>
          <div style={{ color: 'var(--brand-color)', textTransform: 'uppercase', letterSpacing: '0.1em', fontSize: '0.8rem', fontWeight: 600, marginBottom: '1.5rem' }}>
            {ROLE_LABELS[user.role] || user.role}
          </div>

          <div style={{ width: '100%', borderTop: '1px solid var(--border-color)', margin: '1rem 0' }}></div>

          <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status</span>
            <button 
              onClick={() => setOnDuty(!onDuty)}
              className="btn" 
              style={{ 
                padding: '4px 12px', fontSize: '0.8rem', fontWeight: 600,
                background: onDuty ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                color: onDuty ? '#10b981' : '#ef4444',
                border: `1px solid ${onDuty ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`
              }}
            >
              {onDuty ? 'ON DUTY' : 'OFF DUTY'}
            </button>
          </div>
          
          <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
            <span style={{ color: 'var(--text-muted)' }}>Clearance</span>
            <span style={{ fontWeight: 600 }}>Level 2 (Field)</span>
          </div>
        </div>

        {/* Security Settings (Placeholder) */}
        <div className="card">
          <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Shield size={18} color="var(--brand-color)" /> Account Security
          </h3>
          
          <form style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>Current Password</label>
              <input type="password" placeholder="••••••••" className="input-field" disabled />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>New Password</label>
              <input type="password" placeholder="Leave blank to keep current" className="input-field" disabled />
            </div>
            <button className="btn btn-outline" disabled style={{ marginTop: '0.5rem', width: 'fit-content' }}>
              Update Security
            </button>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              * Password changes are currently managed by the System Administrator.
            </p>
          </form>
        </div>

      </div>
    </div>
  );
}
