import { useState, useEffect } from 'react';
import axios from 'axios';
import { PlusCircle, Home, Pencil, Trash2, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function EditHouseholdModal({ household, onClose, onSaved }) {
  const [form, setForm] = useState({
    owner_name: household.owner_name,
    address: household.address,
    phone: household.phone,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await axios.patch(`/api/admin/households/${household.id}`, form);
      onSaved();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)' }}>
      <div className="card animate-slide-in" style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
          <h3>Edit Household</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={20} /></button>
        </div>
        {error && <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: '0.9rem' }}>{error}</div>}
        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.9rem' }}>Owner Name</label>
            <input className="input-field" required value={form.owner_name} onChange={e => setForm({ ...form, owner_name: e.target.value })} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.9rem' }}>Address</label>
            <input className="input-field" required value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: '0.9rem' }}>Phone Number</label>
            <input className="input-field" required value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={saving} style={{ marginTop: '0.5rem' }}>
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function Households() {
  const [households, setHouseholds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const navigate = useNavigate();

  const fetchHouseholds = () => {
    axios.get('/api/admin/households')
      .then(res => setHouseholds(res.data))
      .catch(() => setHouseholds([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchHouseholds(); }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Remove this household? Its past events will be kept but unlinked.')) return;
    setDeletingId(id);
    try {
      await axios.delete(`/api/admin/households/${id}`);
      fetchHouseholds();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete household');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="animate-slide-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Home size={28} color="var(--brand-color)" />
          Registered Households
        </h1>
        <button className="btn btn-primary" onClick={() => navigate('/signup/household')}>
          <PlusCircle size={18} /> Add New Household
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Owner Name</th>
                <th>Physical Address</th>
                <th>Phone Number</th>
                <th>Map Coordinates</th>
                <th>Device Token</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>Loading households...</td></tr>
              ) : households.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No households registered yet. <br/><br/>
                    <button className="btn btn-outline" onClick={() => navigate('/signup/household')}>Register First Device</button>
                  </td>
                </tr>
              ) : (
                households.map(h => (
                  <tr key={h.id}>
                    <td style={{ fontWeight: 500 }}>{h.owner_name}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{h.address}</td>
                    <td>{h.phone}</td>
                    <td style={{ fontSize: '0.85rem', fontFamily: 'monospace' }}>{h.lat.toFixed(4)}, {h.lng.toFixed(4)}</td>
                    <td><code style={{ background: 'rgba(255,255,255,0.05)', padding: '0.2rem 0.5rem', borderRadius: '4px', color: 'var(--brand-color)' }}>{h.device_token}</code></td>
                    <td><span className="badge badge-resolved">Active</span></td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        <button className="btn btn-outline" style={{ padding: '4px 10px', fontSize: '0.8rem' }} onClick={() => setEditing(h)} title="Edit">
                          <Pencil size={14} />
                        </button>
                        <button
                          className="btn btn-outline"
                          style={{ padding: '4px 10px', fontSize: '0.8rem', color: '#ef4444', borderColor: '#ef4444' }}
                          onClick={() => handleDelete(h.id)}
                          disabled={deletingId === h.id}
                          title="Delete"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {editing && (
        <EditHouseholdModal
          household={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); fetchHouseholds(); }}
        />
      )}
    </div>
  );
}
