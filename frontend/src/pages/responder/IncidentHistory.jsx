import { useState, useEffect } from 'react';
import axios from 'axios';
import { History, Search } from 'lucide-react';

export default function IncidentHistory({ user }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    // Fetch all resolved events
    axios.get('/api/events?outcome=resolved')
      .then(res => {
        // Filter to only those responded by this user (or this role category if general history is preferred)
        const myHistory = res.data.filter(a => a.responder_name === user.username);
        setHistory(myHistory);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [user.username]);

  const filtered = history.filter(h => 
    h.location?.address?.toLowerCase().includes(search.toLowerCase()) || 
    h.id.toString().includes(search)
  );

  return (
    <div className="animate-slide-in">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <History size={24} /> Incident History
        </h1>
        
        <div style={{ position: 'relative', width: '250px' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
          <input 
            type="text" 
            placeholder="Search address or ID..." 
            className="input-field" 
            style={{ paddingLeft: '35px' }}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading history...</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            {search ? 'No incidents matched your search.' : 'You have not responded to any incidents yet.'}
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Incident ID</th>
                  <th>Date & Time</th>
                  <th>Location</th>
                  <th>Outcome</th>
                  <th>Dispatched Details</th>
                  <th>Resolution Notes</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(inc => (
                  <tr key={inc.id}>
                    <td><strong>#{inc.id}</strong></td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      {new Date(inc.created_at).toLocaleString()}
                    </td>
                    <td>{inc.location?.address || 'Unknown'}</td>
                    <td><span className="badge badge-resolved">Resolved</span></td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {inc.dispatch_text || 'Standard Dispatch'}
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {inc.responder_notes || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
