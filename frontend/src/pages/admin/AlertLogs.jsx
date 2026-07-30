import { useState, useEffect } from 'react';
import axios from 'axios';
import { Download, Filter } from 'lucide-react';

export default function AlertLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [filterCategory]);

  const fetchLogs = () => {
    setLoading(true);
    let url = '/api/events?limit=200';
    if (filterCategory) url += `&category=${filterCategory}`;
    
    axios.get(url)
      .then(res => setLogs(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const getBadgeClass = (category) => {
    if(category === 'fire') return 'badge badge-active';
    if(category === 'health') return 'badge badge-resolved';
    return 'badge badge-cancelled';
  };

  return (
    <div className="animate-slide-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Event Audit Logs</h1>
        <button className="btn btn-outline">
          <Download size={16} /> Export CSV
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.02)', display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <Filter size={18} color="var(--text-muted)" />
          <select 
            className="input-field" 
            style={{ width: '200px', padding: '0.5rem' }}
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="health">Healthcare</option>
            <option value="fire">Fire</option>
            <option value="police">Police / Danger</option>
          </select>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Category</th>
                <th>Detected Keyword</th>
                <th>Outcome</th>
                <th>Responder</th>
                <th>Responded At</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="7" style={{ textAlign: 'center' }}>Loading logs...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No records found.</td></tr>
              ) : (
                logs.map(log => (
                  <tr key={log.id}>
                    <td style={{ color: 'var(--text-muted)' }}>{new Date(log.timestamp).toLocaleString()}</td>
                    <td>
                      <span className={getBadgeClass(log.category)}>
                        {log.category || 'general'}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'monospace', color: 'var(--brand-color)' }}>"{log.keyword}"</td>
                    <td>
                      <span style={{ color: log.outcome === 'activated' ? 'var(--fire-color)' : 'var(--text-muted)' }}>
                        {log.outcome.toUpperCase()}
                      </span>
                    </td>
                    <td>{log.responder_name || '-'}</td>
                    <td style={{ color: 'var(--text-muted)' }}>
                      {log.responded_at ? new Date(log.responded_at).toLocaleTimeString() : '-'}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{log.responder_notes || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
