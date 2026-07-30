import { useState, useEffect } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Activity, ShieldAlert, CheckCircle, MapPin, Info, Clock, Navigation } from 'lucide-react';
import BaseMap from '../../components/BaseMap';

export default function Overview() {
  const [stats, setStats] = useState(null);
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);

  useEffect(() => {
    // Fetch stats
    axios.get('/api/events/stats')
      .then(res => setStats(res.data))
      .catch(console.error);

    // Fetch active alerts for map
    axios.get('/api/events?outcome=activated&limit=50')
      .then(res => setActiveAlerts(res.data))
      .catch(console.error);
  }, []);

  const getAlertColor = (category) => {
    switch(category) {
      case 'fire': return 'var(--fire-color)';
      case 'health': return 'var(--health-color)';
      default: return 'var(--police-color)';
    }
  };

  return (
    <div className="animate-slide-in">
      <h1 style={{ marginBottom: '2rem' }}>System Overview</h1>
      
      {/* Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', color: 'var(--fire-color)' }}>
            <Activity size={28} />
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Active / Pending Alerts</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{stats?.pending || 0}</div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '12px', color: 'var(--health-color)' }}>
            <CheckCircle size={28} />
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Responded Events</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{stats?.responded || 0}</div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(234, 179, 8, 0.1)', borderRadius: '12px', color: 'var(--brand-color)' }}>
            <ShieldAlert size={28} />
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Total Incidents Logged</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{stats?.total || 0}</div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '12px', color: 'var(--police-color)' }}>
            <Clock size={28} />
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Avg. Response Time</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>
              {stats?.avg_response_seconds != null ? `${stats.avg_response_seconds}s` : '—'}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>SRS target: ≤ 8s</div>
          </div>
        </div>
      </div>

      {/* Global Map & Legend Layout */}
      <div style={{ display: 'flex', gap: '1.5rem', height: '400px' }}>
        
        {/* Left Panel: The Map */}
        <div className="card" style={{ padding: 0, overflow: 'hidden', flex: 2, display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.02)' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
              <MapPin size={18} color="var(--brand-color)" /> Active Incident Geolocation
            </h3>
          </div>
          <div style={{ flex: 1, position: 'relative' }}>
            <BaseMap 
              markers={activeAlerts.filter(a => a.location).map(a => ({
                id: a.id,
                lat: a.location.lat,
                lng: a.location.lng,
                type: a.category,
                label: `Incident #${a.id}`,
                sublabel: a.location.owner_name,
                meta: {
                  Address: a.location.address,
                  Phone: a.location.phone,
                  'Clap Count': a.clap_count,
                  Dispatched: new Date(a.created_at).toLocaleTimeString()
                }
              }))}
              heatmapPoints={activeAlerts.filter(a => a.location).map(a => [a.location.lat, a.location.lng, 1.0])}
              triangulate={true}
              onMarkerClick={(m) => setSelectedIncident(activeAlerts.find(a => a.id === m.id))}
            />
          </div>
        </div>

        {/* Right Panel: Selected Details */}
        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
            <Info size={18} color="var(--brand-color)"/> Incident Dispatch Context
          </h3>
          
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {selectedIncident ? (
              <div className="animate-slide-in">
                <h4 style={{ color: getAlertColor(selectedIncident.category), textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                  {selectedIncident.category} DISPATCH
                </h4>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                  <strong>Resident:</strong> {selectedIncident.location?.owner_name || 'Unknown'}
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                  <span><strong>Address:</strong> {selectedIncident.location?.address || 'Coordinates only'}</span>
                  {selectedIncident.location && (
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${selectedIncident.location.lat},${selectedIncident.location.lng}`}
                      target="_blank" rel="noopener noreferrer"
                      style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--brand-color)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                    >
                      <Navigation size={13} /> Directions
                    </a>
                  )}
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                  <strong>Phone:</strong> {selectedIncident.location?.phone || 'N/A'}
                </div>
                {selectedIncident.modifier_phrase && (
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                    <strong>Reported:</strong> "{selectedIncident.modifier_phrase}"
                  </div>
                )}
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '1rem', fontStyle: 'italic', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: 8, border: '1px solid var(--border-color)' }}>
                  {selectedIncident.dispatch_text || `Emergency keyword triggered: "${selectedIncident.keyword}"`}
                </div>
              </div>
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', fontSize: '0.9rem', padding: '1rem' }}>
                Select a marker on the map to view detailed incident context and household information.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
