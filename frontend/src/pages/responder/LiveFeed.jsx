import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Clock, ShieldAlert, CheckCircle, Activity, BellRing, Navigation, FileText } from 'lucide-react';
import BaseMap from '../../components/BaseMap';

// --- Sound Alarm Helper ----------------------------------------------------
const beepBase64 = "data:audio/wav;base64,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"

let alarmAudio = null;
function playAlarm() {
  if (!alarmAudio) {
    alarmAudio = new Audio(beepBase64);
    alarmAudio.loop = true;
    alarmAudio.volume = 0.6;
  }
  alarmAudio.play().catch(e => console.log('Audio blocked by browser:', e));
}
function stopAlarm() {
  if (alarmAudio) alarmAudio.pause();
}

// --- Per-role SOP checklist --------------------------------------------------
// Real dispatch workflows differ by service; this replaces one identical
// checklist shared by fire/health/police with role-appropriate steps.
const SOP_STEPS = {
  fire_responder: [
    { key: 'enRoute',   label: 'Unit En Route' },
    { key: 'arrived',   label: 'Arrived on Scene' },
    { key: 'contained', label: 'Fire Contained / Scene Safe' },
  ],
  health_responder: [
    { key: 'enRoute',  label: 'Unit En Route' },
    { key: 'arrived',  label: 'Arrived on Scene' },
    { key: 'assessed', label: 'Patient Assessed' },
  ],
  police_responder: [
    { key: 'enRoute', label: 'Unit En Route' },
    { key: 'arrived', label: 'Arrived on Scene' },
    { key: 'secured', label: 'Scene Secured' },
  ],
};
const DEFAULT_SOP_STEPS = [
  { key: 'enRoute', label: 'Unit En Route' },
  { key: 'arrived', label: 'Arrived on Scene' },
];

// --- Wait-time aging badge ---------------------------------------------------
function waitBadge(createdAt, now) {
  const elapsed = Math.max(0, Math.floor((now - new Date(createdAt).getTime()) / 1000));
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;
  const label = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  const color = elapsed >= 180 ? '#ef4444' : elapsed >= 60 ? '#eab308' : '#10b981';
  return { label, color };
}

function directionsUrl(location) {
  if (!location || typeof location.lat !== 'number' || typeof location.lng !== 'number') return null;
  return `https://www.google.com/maps/dir/?api=1&destination=${location.lat},${location.lng}`;
}

// ---------------------------------------------------------------------------

export default function LiveFeed({ user }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alarmActive, setAlarmActive] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  const [notesDraft, setNotesDraft] = useState({});
  const [conflictMsg, setConflictMsg] = useState('');
  const flashInterval = useRef(null);
  const sopSteps = SOP_STEPS[user.role] || DEFAULT_SOP_STEPS;

  const refetchAlerts = () => {
    const rolePrefix = user.role.split('_')[0];
    axios.get(`/api/events?outcome=activated,acknowledged`)
      .then(res => {
        const myAlerts = res.data.filter(a => a.category === rolePrefix || (a.category === 'police' && rolePrefix === 'police'));
        setAlerts(myAlerts);
      })
      .catch(console.error);
  };

  // --- Live wait-time ticker -------------------------------------------------
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  // --- WebSocket Connection ------------------------------------------------
  useEffect(() => {
    // Request desktop notification permission on load
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsBase}/ws/responder`);

    ws.onopen = () => console.log("Responder CAD Connected");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'emergency_alert') {
        const newAlert = data;
        // Only accept if matches my role category
        const rolePrefix = user.role.split('_')[0];
        if (newAlert.category === rolePrefix || (newAlert.category === 'police' && rolePrefix === 'police')) {
          setAlerts(prev => [newAlert, ...prev]);
          triggerAlarm(newAlert);
        }
      } else if (data.type === 'status_update') {
        // Multi-unit awareness: another responder (possibly on a different
        // browser) acknowledged/resolved an incident -- reflect it live so
        // this console never shows a stale "still incoming" alert.
        if (data.outcome === 'resolved') {
          setAlerts(prev => prev.filter(a => a.id !== data.id));
        } else {
          setAlerts(prev => prev.map(a => a.id === data.id
            ? { ...a, outcome: data.outcome, responder_name: data.responder_name, responded_at: data.responded_at }
            : a));
        }
      }
    };

    // Fetch initial active alerts
    axios.get(`/api/events?outcome=activated,acknowledged`)
      .then(res => {
        const rolePrefix = user.role.split('_')[0];
        // Only accept if matches my role category (or police fallback for testing)
        const myAlerts = res.data.filter(a => a.category === rolePrefix || (a.category === 'police' && rolePrefix === 'police'));
        setAlerts(myAlerts);
        // If there are unacknowledged alerts, trigger alarm
        if (myAlerts.some(a => a.outcome !== 'acknowledged')) {
          triggerAlarm(myAlerts[0]);
        }
      })
      .finally(() => setLoading(false));

    return () => { ws.close(); stopAlarm(); clearInterval(flashInterval.current); };
  }, [user]);

  // --- Alarm Logic ---------------------------------------------------------
  const triggerAlarm = (alert) => {
    if (alarmActive) return;
    setAlarmActive(true);
    playAlarm();

    if (Notification.permission === 'granted') {
      new Notification(`NEW ${alert.category.toUpperCase()} EMERGENCY!`, {
        body: `Location: ${alert.location?.address || 'Unknown'}`,
      });
    }

    if (!flashInterval.current) {
      let toggle = false;
      flashInterval.current = setInterval(() => {
        document.title = toggle ? 'EMERGENCY DISPATCH!' : 'MTEAS Responder';
        toggle = !toggle;
      }, 800);
    }
  };

  const silenceAlarm = () => {
    setAlarmActive(false);
    stopAlarm();
    clearInterval(flashInterval.current);
    flashInterval.current = null;
    document.title = 'MTEAS Responder CAD';
  };

  // --- Actions -------------------------------------------------------------
  const handleAcknowledge = async (id) => {
    setConflictMsg('');
    try {
      await axios.patch(`/api/events/${id}/status`, {
        status: 'acknowledged',
        responder_name: user.username
      });
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, outcome: 'acknowledged', responder_name: user.username } : a));

      // Stop alarm if no more unacknowledged alerts
      const stillUnacked = alerts.filter(a => a.id !== id && a.outcome !== 'acknowledged');
      if (stillUnacked.length === 0) silenceAlarm();
    } catch (e) {
      if (e.response?.status === 409) {
        setConflictMsg(e.response.data?.detail || 'Another unit already took this incident.');
        refetchAlerts();
      } else {
        console.error(e);
      }
    }
  };

  const handleToggleSop = (id, field) => {
    setAlerts(prev => prev.map(a => {
      if (a.id === id) {
        return { ...a, sop: { ...(a.sop || {}), [field]: !a.sop?.[field] } };
      }
      return a;
    }));
  };

  const handleResolve = async (id) => {
    try {
      await axios.patch(`/api/events/${id}/status`, { status: 'resolved', notes: notesDraft[id] || '' });
      setAlerts(prev => prev.filter(a => a.id !== id));
      setNotesDraft(prev => { const next = { ...prev }; delete next[id]; return next; });
    } catch (e) {
      console.error(e);
    }
  };

  // --- Layout --------------------------------------------------------------
  // Oldest-first: the longer an alert has waited, the higher its priority.
  const unacknowledged = alerts
    .filter(a => a.outcome !== 'acknowledged')
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  const active = alerts.filter(a => a.outcome === 'acknowledged');

  return (
    <div className={`animate-slide-in ${alarmActive ? 'alarm-pulse-bg' : ''}`} style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {alarmActive && (
        <style>{`
          .alarm-pulse-bg { animation: pulseRed 1.5s infinite; }
          @keyframes pulseRed { 0%, 100% { box-shadow: inset 0 0 0px 4px rgba(239,68,68,0); } 50% { box-shadow: inset 0 0 0px 4px rgba(239,68,68,0.8); } }
        `}</style>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexShrink: 0 }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: alarmActive ? '#ef4444' : 'var(--text-main)' }}>
          <Activity size={24} /> CAD Terminal
        </h1>
        {alarmActive && (
          <button className="btn btn-primary" onClick={silenceAlarm} style={{ background: '#ef4444', color: '#fff', border: 'none', animation: 'pulse 1.5s infinite' }}>
            <BellRing size={16}/> Silence Alarm
          </button>
        )}
      </div>

      {conflictMsg && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', borderRadius: 8, background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.3)', color: '#eab308', fontSize: '0.9rem', flexShrink: 0 }}>
          {conflictMsg}
        </div>
      )}

      <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>

        {/* Left: Map */}
        <div className="card" style={{ flex: 1.5, padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <BaseMap
            markers={alerts.filter(a => a.location).map(a => ({
              id: a.id,
              lat: a.location.lat,
              lng: a.location.lng,
              type: a.category,
              label: `Dispatch #${a.id}`,
              sublabel: a.location.address,
              meta: { Phone: a.location.phone, Time: new Date(a.created_at).toLocaleTimeString() }
            }))}
            triangulate={true}
          />
        </div>

        {/* Right: Dispatch Queues */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', minHeight: 0 }}>

          {/* Top: Incoming (Unacknowledged), oldest-first priority order */}
          <div className="card" style={{ flex: unacknowledged.length > 0 ? '1 1 0' : '0 0 auto', display: 'flex', flexDirection: 'column', minHeight: 0, border: unacknowledged.length > 0 ? '1px solid #ef4444' : '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: '1rem', color: unacknowledged.length > 0 ? '#ef4444' : 'var(--text-muted)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
              <ShieldAlert size={18} /> Incoming Queue ({unacknowledged.length})
            </h3>
            <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
              {unacknowledged.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '1rem' }}>No incoming alerts.</div>
              ) : (
                unacknowledged.map(alert => {
                  const badge = waitBadge(alert.created_at, now);
                  const dirUrl = directionsUrl(alert.location);
                  return (
                    <div key={alert.id} style={{ padding: '1rem', background: 'rgba(239,68,68,0.1)', borderRadius: 8, marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <strong style={{ color: '#ef4444', textTransform: 'uppercase' }}>Dispatch #{alert.id}</strong>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '2px 8px', borderRadius: 999, background: `${badge.color}22`, color: badge.color }}>
                          waiting {badge.label}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.9rem', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                        <span><strong>Address:</strong> {alert.location?.address || 'Unknown'}</span>
                        {dirUrl && (
                          <a href={dirUrl} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--blue, #3b82f6)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                            <Navigation size={13} /> Directions
                          </a>
                        )}
                      </div>
                      {alert.modifier_phrase && (
                        <div style={{ fontSize: '0.9rem', marginBottom: '1rem', padding: '0.5rem 0.75rem', background: 'rgba(239,68,68,0.15)', borderRadius: 6 }}>
                          <strong>Reported:</strong> "{alert.modifier_phrase}"
                        </div>
                      )}
                      <button className="btn btn-primary" onClick={() => handleAcknowledge(alert.id)} style={{ width: '100%', justifyContent: 'center' }}>
                        Acknowledge Incident
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Bottom: Active (Acknowledged) */}
          <div className="card" style={{ flex: '2 1 0', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
              <CheckCircle size={18} color="var(--brand-color)" /> Active / Responding ({active.length})
            </h3>
            <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
              {active.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '1rem' }}>No active incidents.</div>
              ) : (
                active.map(alert => {
                  const dirUrl = directionsUrl(alert.location);
                  const allDone = sopSteps.every(s => alert.sop?.[s.key]);
                  return (
                    <div key={alert.id} style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 8, marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <strong style={{ color: 'var(--brand-color)' }}>Incident #{alert.id}</strong>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}><Clock size={12} style={{ display:'inline', marginBottom:-2 }}/> {new Date(alert.created_at).toLocaleTimeString()}</span>
                      </div>

                      {alert.responder_name && (
                        <div style={{ fontSize: '0.8rem', marginBottom: '0.5rem', color: alert.responder_name === user.username ? 'var(--brand-color)' : 'var(--text-muted)' }}>
                          Acknowledged by: <strong>{alert.responder_name}{alert.responder_name === user.username ? ' (you)' : ''}</strong>
                        </div>
                      )}

                      <div style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}><strong>Resident:</strong> {alert.location?.owner_name}</div>
                      <div style={{ fontSize: '0.9rem', marginBottom: '0.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                        <span><strong>Address:</strong> {alert.location?.address}</span>
                        {dirUrl && (
                          <a href={dirUrl} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--blue, #3b82f6)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                            <Navigation size={13} /> Directions
                          </a>
                        )}
                      </div>
                      <div style={{ fontSize: '0.9rem', marginBottom: '1rem' }}><strong>Phone:</strong> {alert.location?.phone}</div>

                      {alert.modifier_phrase && (
                        <div style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                          <strong style={{ color: 'var(--text-muted)' }}>Reported:</strong> "{alert.modifier_phrase}"
                        </div>
                      )}
                      <div style={{ padding: '0.75rem', background: 'rgba(0,0,0,0.3)', borderRadius: 6, marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        <strong>Dispatch Notes:</strong> {alert.dispatch_text || `Trigger: "${alert.keyword}" (${alert.clap_count} claps)`}
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <strong style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Standard Operating Procedure</strong>
                        {sopSteps.map((step, i) => {
                          const prevDone = i === 0 || alert.sop?.[sopSteps[i - 1].key];
                          return (
                            <label key={step.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.4rem', cursor: 'pointer', fontSize: '0.9rem' }}>
                              <input
                                type="checkbox"
                                checked={alert.sop?.[step.key] || false}
                                onChange={() => handleToggleSop(alert.id, step.key)}
                                disabled={!prevDone}
                              /> {step.label}
                            </label>
                          );
                        })}
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                          <FileText size={14} /> Resolution Notes (optional)
                        </label>
                        <textarea
                          className="input-field"
                          rows={2}
                          placeholder="What happened / outcome for the record…"
                          value={notesDraft[alert.id] || ''}
                          onChange={e => setNotesDraft(prev => ({ ...prev, [alert.id]: e.target.value }))}
                          style={{ resize: 'vertical', fontFamily: 'inherit' }}
                        />
                      </div>

                      <button
                        className="btn btn-outline"
                        disabled={!allDone}
                        onClick={() => handleResolve(alert.id)}
                        style={{ width: '100%', justifyContent: 'center', borderColor: allDone ? '#10b981' : 'var(--border-color)', color: allDone ? '#10b981' : 'var(--text-muted)' }}
                      >
                        <CheckCircle size={16}/> Mark as Resolved
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
