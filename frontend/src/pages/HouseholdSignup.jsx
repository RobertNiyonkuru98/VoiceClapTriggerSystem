import { useState, useEffect } from 'react';
import axios from 'axios';
import { Home, MapPin, Copy, Siren, ArrowLeft } from 'lucide-react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';

// Fix broken default marker icons in Vite production builds
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function LocationPicker({ position, setPosition }) {
  useMapEvents({ click(e) { setPosition(e.latlng); } });
  return position === null ? null : <Marker position={position} />;
}

function MapUpdater({ position }) {
  const map = useMap();
  useEffect(() => {
    if (position) map.setView([position.lat, position.lng], 15);
  }, [position, map]);
  return null;
}

export default function HouseholdSignup() {
  const [form, setForm] = useState({ owner_name: '', address: '', phone: '' });
  const [position, setPosition] = useState(null); // {lat, lng}
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    // Try to get browser location initially
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        pos => setPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        err => console.log("Geolocation error:", err)
      );
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!position) {
      setError("Please pick a location on the map.");
      return;
    }
    setLoading(true);
    setError('');
    
    try {
      const res = await axios.post('/api/auth/signup/household', {
        ...form,
        lat: position.lat,
        lng: position.lng
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="container flex-center" style={{ minHeight: '80vh', flexDirection: 'column', gap: 0 }}>
        <div className="card" style={{ width: '100%', maxWidth: '500px', textAlign: 'center' }}>
          <h2 style={{ color: 'var(--health-color)', marginBottom: '1rem' }}>Registration Successful</h2>
          <p>Household for <b>{result.owner_name}</b> has been registered.</p>
          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '6px', margin: '1.5rem 0' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>Device Registration Token:</p>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
              <code style={{ color: 'var(--brand-color)', fontSize: '1.1rem' }}>{result.device_token}</code>
              <button className="btn" style={{ padding: '0.2rem 0.5rem' }} onClick={() => navigator.clipboard.writeText(result.device_token)}>
                <Copy size={16}/>
              </button>
            </div>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Enter this token in the Settings tab of the MTEAS Desktop application to link the device to this household.
          </p>
          <a href="/login" className="btn btn-primary" style={{ marginTop: '1.5rem', textDecoration: 'none' }}>Go to Dashboard</a>
        </div>
        <div style={{ marginTop: '1.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', opacity: 0.55, textAlign: 'center' }}>
          © 2026 Tony Robert · MTEAS
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingBottom: '3rem' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', paddingTop: '1rem' }}>
        <a href="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: '0.9rem', textDecoration: 'none', marginBottom: '1rem' }}>
          <ArrowLeft size={15} /> Back to Login
        </a>
      </div>
      <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <Siren size={36} color="var(--brand-color)" style={{ marginBottom: '0.25rem' }} />
          <div><span className="brand-font">MTEAS</span></div>
        </div>
        <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
          <Home /> Register Household Device
        </h2>
        
        {error && <div className="alert-card alert-fire" style={{ padding: '1rem', marginBottom: '1rem', background: 'rgba(239, 68, 68, 0.1)' }}>{error}</div>}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Owner Name</label>
              <input 
                type="text" 
                className="input-field" 
                required
                value={form.owner_name}
                onChange={e => setForm({...form, owner_name: e.target.value})}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Phone Number</label>
              <input 
                type="text" 
                className="input-field" 
                required
                value={form.phone}
                onChange={e => setForm({...form, phone: e.target.value})}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Physical Address</label>
            <input 
              type="text" 
              className="input-field" 
              required
              value={form.address}
              onChange={e => setForm({...form, address: e.target.value})}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
              <MapPin size={16} style={{ verticalAlign: 'middle', marginRight: '4px' }}/> 
              Map Location (Click to set pin)
            </label>
            <div style={{ height: '300px', borderRadius: '8px', overflow: 'hidden' }}>
              <MapContainer
                center={[-1.9441, 30.0619]}
                zoom={13}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <LocationPicker position={position} setPosition={setPosition} />
                <MapUpdater position={position} />
              </MapContainer>
            </div>
            {position && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--brand-color)' }}>
                Selected: {position.lat.toFixed(5)}, {position.lng.toFixed(5)}
              </div>
            )}
          </div>
          
          <button type="submit" className="btn btn-primary" disabled={loading} style={{ padding: '0.75rem' }}>
            {loading ? 'Registering...' : 'Register Household & Generate Token'}
          </button>
        </form>
        </div>
      <div style={{ maxWidth: '800px', margin: '1.5rem auto 0', fontSize: '0.75rem', color: 'var(--text-muted)', opacity: 0.55, textAlign: 'center' }}>
        © 2026 Tony Robert · MTEAS
      </div>
    </div>
  );
}
