import { useState, useEffect } from 'react';
import axios from 'axios';
import { Terminal, RefreshCcw, AlertTriangle, Info, AlertCircle } from 'lucide-react';

const SEVERITY_CONFIG = {
  INFO:  { color: '#10b981', Icon: Info },
  WARN:  { color: '#eab308', Icon: AlertTriangle },
  ERROR: { color: '#ef4444', Icon: AlertCircle },
};

export default function SystemLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [severity, setSeverity] = useState('');

  const fetchLogs = () => {
    setLoading(true);
    const params = severity ? `?severity=${severity}` : '';
    axios.get(`/api/admin/logs${params}`)
      .then(r => setLogs(r.data))
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchLogs(); }, [severity]); // eslint-disable-line

  return (
    <div className="animate-slide-in">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Terminal size={24} /> System Logs
        </h1>
        <button className="btn btn-outline" onClick={fetchLogs} style={{ gap: 6 }}>
          <RefreshCcw size={15} /> Refresh
        </button>
      </div>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.95rem' }}>
        Structured server-side event log — auth events, dispatch activity, and system errors.
      </p>

      {/* Severity Filter */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {['', 'INFO', 'WARN', 'ERROR'].map(s => (
          <button
            key={s}
            onClick={() => setSeverity(s)}
            style={{
              padding: '0.4rem 1rem', borderRadius: 8, border: '1px solid var(--border-color)',
              cursor: 'pointer', fontFamily: 'Outfit, sans-serif', fontSize: '0.85rem', fontWeight: 600,
              background: severity === s ? 'var(--brand-color)' : 'transparent',
              color: severity === s ? '#111827' : 'var(--text-muted)',
              transition: 'all 0.2s ease',
            }}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '2rem', color: 'var(--text-muted)', textAlign: 'center' }}>Loading logs…</div>
        ) : logs.length === 0 ? (
          <div style={{ padding: '2rem', color: 'var(--text-muted)', textAlign: 'center' }}>No log entries found.</div>
        ) : (
          logs.map((log, i) => {
            const cfg = SEVERITY_CONFIG[log.severity] || SEVERITY_CONFIG.INFO;
            return (
              <div
                key={log.id}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: '1rem',
                  padding: '0.85rem 1.25rem',
                  borderBottom: i < logs.length - 1 ? '1px solid var(--border-color)' : 'none',
                  borderLeft: `3px solid ${cfg.color}`,
                  background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                  transition: 'background 0.2s',
                }}
              >
                {/* Severity icon */}
                <cfg.Icon size={16} color={cfg.color} style={{ marginTop: 2, flexShrink: 0 }} />

                {/* Message */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', marginBottom: 3 }}>
                    <span style={{ fontWeight: 700, fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: cfg.color }}>
                      {log.severity}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'monospace', background: 'rgba(255,255,255,0.04)', padding: '1px 7px', borderRadius: 4 }}>
                      {log.source}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-main)', fontSize: '0.9rem' }}>{log.message}</div>
                </div>

                {/* Timestamp */}
                <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', whiteSpace: 'nowrap', flexShrink: 0 }}>
                  {new Date(log.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  <br />
                  <span style={{ fontSize: '0.72rem' }}>{new Date(log.ts).toLocaleDateString()}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
