import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Activity, History, User, LogOut } from 'lucide-react';
import axios from 'axios';

const NAV_STYLE = {
  display: 'flex', alignItems: 'center', gap: '0.6rem',
  padding: '0.65rem 1rem', borderRadius: 8, fontFamily: 'Outfit, sans-serif',
  fontWeight: 500, fontSize: '0.95rem', cursor: 'pointer',
  transition: 'all 0.2s ease', border: 'none', width: '100%',
};

function SideLink({ to, end, icon: Icon, children }) {
  return (
    <NavLink
      to={to}
      end={end}
      style={({ isActive }) => ({
        ...NAV_STYLE,
        textDecoration: 'none',
        background: isActive ? 'var(--brand-color)' : 'transparent',
        color: isActive ? '#111827' : 'var(--text-muted)',
      })}
    >
      <Icon size={18} /> {children}
    </NavLink>
  );
}

export default function ResponderLayout({ user, setUser }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    navigate('/login');
  };

  const roleLabels = {
    health_responder: 'Medical Unit',
    fire_responder: 'Fire Unit',
    police_responder: 'Police Unit'
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div style={{ padding: '1.5rem', textAlign: 'center', borderBottom: '1px solid var(--border-color)' }}>
          <span className="brand-font">MTEAS</span>
          <div style={{ fontSize: '0.75rem', color: 'var(--brand-color)', marginTop: '0.2rem', textTransform: 'uppercase', letterSpacing: '1.5px', fontWeight: 600 }}>
            {roleLabels[user.role] || 'Responder'}
          </div>
        </div>

        <nav style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', padding: '0.5rem 1rem', marginBottom: '0.25rem' }}>
            Dispatch
          </div>
          <SideLink to="/responder" end icon={Activity}>Live Feed</SideLink>
          <SideLink to="/responder/history" icon={History}>Incident History</SideLink>

          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', padding: '0.5rem 1rem', marginTop: '1rem', marginBottom: '0.25rem' }}>
            Account
          </div>
          <SideLink to="/responder/profile" icon={User}>My Profile</SideLink>
          
          <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
            <button onClick={handleLogout} style={{ ...NAV_STYLE, background: 'transparent', color: '#ef4444' }}>
              <LogOut size={18} /> Logout
            </button>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.75rem', opacity: 0.6 }}>
              Created by Tony Robert · 2026
            </div>
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="main-content">
        {/* Topbar */}
        <header className="topbar">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 500, color: 'var(--text-muted)' }}>
            Responder CAD Terminal
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Unit: <strong style={{ color: 'var(--text-main)' }}>{user.username}</strong>
            </span>
            <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: 'var(--brand-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#111827', fontSize: '0.9rem' }}>
              {user.username.charAt(0).toUpperCase()}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
