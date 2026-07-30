import { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, Plus, ShieldCheck, ShieldOff, Terminal, Settings2, Trash2, Database, X } from 'lucide-react';

// ── Helper ──────────────────────────────────────────────────────────────────
const ROLE_LABELS = {
  admin:            { label: 'Administrator', color: '#eab308' },
  health_responder: { label: 'Health / Medical', color: '#10b981' },
  fire_responder:   { label: 'Fire Responder',   color: '#ef4444' },
  police_responder: { label: 'Police / Security', color: '#3b82f6' },
};

function RoleBadge({ role }) {
  const cfg = ROLE_LABELS[role] || { label: role, color: '#a1a1aa' };
  return (
    <span style={{
      padding: '3px 10px', borderRadius: 999, fontSize: '0.78rem',
      fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
      background: cfg.color + '22', color: cfg.color,
      border: `1px solid ${cfg.color}44`,
    }}>
      {cfg.label}
    </span>
  );
}

// ── Sub-sections ────────────────────────────────────────────────────────────

function AccountsSection() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', role: 'health_responder' });
  const [creating, setCreating] = useState(false);
  const [msg, setMsg] = useState('');

  const fetchUsers = () => {
    axios.get('/api/admin/users').then(r => setUsers(r.data)).finally(() => setLoading(false));
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await axios.post('/api/admin/users', form);
      setMsg('Account created successfully!');
      setShowModal(false);
      setForm({ username: '', password: '', role: 'health_responder' });
      fetchUsers();
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Failed to create account');
    } finally { setCreating(false); }
  };

  const toggleActive = async (id) => {
    await axios.patch(`/api/admin/users/${id}`);
    fetchUsers();
  };

  return (
    <section>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
          <Users size={20} color="var(--brand-color)" /> Responder Accounts
        </h2>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={16} /> New Account
        </button>
      </div>

      {msg && <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', borderRadius: 8, background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.3)', color: 'var(--brand-color)', fontSize: '0.9rem' }}>{msg}</div>}

      {loading ? <div style={{ color: 'var(--text-muted)' }}>Loading accounts…</div> : (
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td style={{ fontWeight: 600 }}>{u.username}</td>
                  <td><RoleBadge role={u.role} /></td>
                  <td>
                    <span className={`badge ${u.is_active ? 'badge-resolved' : 'badge-cancelled'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    {u.username !== 'admin' && (
                      <button
                        onClick={() => toggleActive(u.id)}
                        className="btn btn-outline"
                        style={{ padding: '4px 12px', fontSize: '0.8rem', gap: 4, color: u.is_active ? '#ef4444' : '#10b981', borderColor: u.is_active ? '#ef4444' : '#10b981' }}
                        title={u.is_active ? 'Deactivate' : 'Reactivate'}
                      >
                        {u.is_active ? <ShieldOff size={14} /> : <ShieldCheck size={14} />}
                        {u.is_active ? 'Deactivate' : 'Reactivate'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Account Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)' }}>
          <div className="card animate-slide-in" style={{ width: '100%', maxWidth: 420 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
              <h3>Create New Account</h3>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={20} /></button>
            </div>
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.9rem' }}>Username</label>
                <input className="input-field" required value={form.username} onChange={e => setForm({...form, username: e.target.value})} />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.9rem' }}>Password</label>
                <input className="input-field" type="password" required value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.9rem' }}>Role</label>
                <select className="input-field" value={form.role} onChange={e => setForm({...form, role: e.target.value})} style={{ cursor: 'pointer' }}>
                  <option value="health_responder">Health / Medical Responder</option>
                  <option value="fire_responder">Fire Responder</option>
                  <option value="police_responder">Police / Security Responder</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary" disabled={creating} style={{ marginTop: '0.5rem' }}>
                {creating ? 'Creating…' : 'Create Account'}
              </button>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}

function ConfigSection() {
  const [config, setConfig] = useState(null);
  useEffect(() => {
    axios.get('/api/admin/config').then(r => setConfig(r.data)).catch(() => {});
  }, []);

  const rows = config ? [
    ['App Version',    config.app_version],
    ['Database',       config.database_url],
    ['CORS Origins',   config.cors_origins?.join(', ')],
    ['JWT Algorithm',  config.jwt_algorithm],
    ['Environment',    config.environment],
    ['Server Time',    config.server_time_utc ? new Date(config.server_time_utc).toLocaleString() : '—'],
  ] : [];

  return (
    <section>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', marginBottom: '1.5rem' }}>
        <Database size={20} color="var(--brand-color)" /> Backend Configuration
      </h2>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {rows.map(([k, v], i) => (
          <div key={k} style={{ display: 'flex', padding: '0.85rem 1.5rem', borderBottom: i < rows.length - 1 ? '1px solid var(--border-color)' : 'none', gap: '1rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', minWidth: 160 }}>{k}</span>
            <span style={{ color: 'var(--text-main)', fontSize: '0.9rem', fontFamily: 'monospace', wordBreak: 'break-all' }}>{v || '—'}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function DangerSection() {
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(null); // 'events' | 'households' | null
  const [msg, setMsg] = useState('');
  const unlocked = confirm === 'CONFIRM';

  const run = async (action, url, label) => {
    setBusy(action);
    setMsg('');
    try {
      const res = await axios.post(url);
      setMsg(`✅ ${label}: ${res.data.deleted_count} record(s) removed.`);
      setConfirm('');
    } catch (err) {
      setMsg(`❌ ${err.response?.data?.detail || 'Action failed'}`);
    } finally {
      setBusy(null);
    }
  };

  return (
    <section>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', marginBottom: '1.5rem', color: '#ef4444' }}>
        <Trash2 size={20} /> Danger Zone
      </h2>
      <div className="card" style={{ border: '1px solid rgba(239,68,68,0.35)', background: 'rgba(239,68,68,0.05)' }}>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          These actions are <strong style={{ color: '#ef4444' }}>irreversible</strong>. They are intended for system administrators managing the live database. Type <code style={{ background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: 4 }}>CONFIRM</code> to enable the buttons.
        </p>
        {msg && <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: msg.startsWith('✅') ? '#10b981' : '#ef4444' }}>{msg}</div>}
        <input
          className="input-field" placeholder='Type "CONFIRM" to unlock'
          value={confirm} onChange={e => setConfirm(e.target.value)}
          style={{ marginBottom: '1rem', maxWidth: 320 }}
        />
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            className="btn"
            disabled={!unlocked || busy !== null}
            onClick={() => { if (window.confirm('Permanently delete ALL event logs?')) run('events', '/api/admin/reset-events', 'Event logs reset'); }}
            style={{ background: unlocked ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.03)', color: unlocked ? '#ef4444' : 'var(--text-muted)', border: '1px solid rgba(239,68,68,0.3)', cursor: unlocked ? 'pointer' : 'not-allowed' }}
            title="Wipe all event logs from the database"
          >
            <Trash2 size={15} /> {busy === 'events' ? 'Resetting…' : 'Reset All Event Logs'}
          </button>
          <button
            className="btn"
            disabled={!unlocked || busy !== null}
            onClick={() => { if (window.confirm('Permanently delete ALL registered households?')) run('households', '/api/admin/wipe-households', 'Households wiped'); }}
            style={{ background: unlocked ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.03)', color: unlocked ? '#ef4444' : 'var(--text-muted)', border: '1px solid rgba(239,68,68,0.3)', cursor: unlocked ? 'pointer' : 'not-allowed' }}
            title="Remove all registered household devices"
          >
            <Trash2 size={15} /> {busy === 'households' ? 'Wiping…' : 'Wipe All Households'}
          </button>
        </div>
      </div>
    </section>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'accounts', label: 'Accounts',     Icon: Users },
  { id: 'config',   label: 'Configuration', Icon: Settings2 },
  { id: 'danger',   label: 'Danger Zone',   Icon: Trash2 },
];

export default function Settings() {
  const [tab, setTab] = useState('accounts');

  return (
    <div className="animate-slide-in">
      <h1 style={{ marginBottom: '0.5rem' }}>System Settings</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.95rem' }}>Manage responder accounts, view backend config, and perform system maintenance.</p>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '2rem', background: 'rgba(255,255,255,0.03)', padding: '4px', borderRadius: 10, border: '1px solid var(--border-color)', width: 'fit-content' }}>
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.55rem 1.1rem', borderRadius: 7, border: 'none', cursor: 'pointer',
              fontFamily: 'Outfit, sans-serif', fontSize: '0.9rem', fontWeight: tab === id ? 600 : 400,
              background: tab === id ? 'var(--brand-color)' : 'transparent',
              color: tab === id ? '#111827' : 'var(--text-muted)',
              transition: 'all 0.2s ease',
            }}
          >
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>

      <div className="card">
        {tab === 'accounts' && <AccountsSection />}
        {tab === 'config'   && <ConfigSection />}
        {tab === 'danger'   && <DangerSection />}
      </div>
    </div>
  );
}
