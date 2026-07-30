/**
 * BaseMap.jsx — Shared reusable Leaflet + OpenStreetMap component for MTEAS.
 * Ported from the E-Vuze pharmacy_front BaseMap.tsx reference.
 *
 * Features:
 *  - Custom teardrop SVG pin icons per category (fire/health/police/household)
 *  - Triangulation dashed polylines between all active incident markers
 *  - Heatmap layer via leaflet.heat CDN plugin
 *  - Floating legend overlay (bottom-left)
 *  - Click-to-popup: detailed card at bottom-center on marker click
 *  - Auto-fits bounds to all markers
 *  - User location blue pulsing dot (optional)
 */

import { useEffect, useRef, useState } from 'react';
import { MapPin, X } from 'lucide-react';

// --- Color config per marker type ------------------------------------------
const MARKER_COLORS = {
  fire:      '#ef4444',
  health:    '#10b981',
  police:    '#3b82f6',
  household: '#eab308',
  user:      '#a855f7',
};

const MARKER_LABELS = {
  fire:      'Fire Emergency',
  health:    'Medical Emergency',
  police:    'Police / Danger',
  household: 'Registered Household',
  user:      'Your Location',
};

// --- Build a teardrop SVG pin as a div-icon HTML string --------------------
function buildPinHtml(color, size = 34, selected = false) {
  const border = selected ? '#ffffff' : 'rgba(0,0,0,0.3)';
  const shadow = selected
    ? `0 0 0 3px ${color}88, 0 4px 16px rgba(0,0,0,0.5)`
    : '0 2px 8px rgba(0,0,0,0.4)';
  return `
    <div style="position:relative;width:${size}px;height:${size}px;filter:drop-shadow(0 3px 6px rgba(0,0,0,0.35));">
      <svg viewBox="0 0 34 42" width="${size}" height="${size * 1.24}" xmlns="http://www.w3.org/2000/svg">
        <path d="M17 0C9.27 0 3 6.27 3 14c0 10.5 14 28 14 28s14-17.5 14-28C31 6.27 24.73 0 17 0z"
          fill="${color}" stroke="${border}" stroke-width="1.5"/>
        <circle cx="17" cy="14" r="6" fill="white" opacity="0.9"/>
      </svg>
      ${selected ? `<div style="position:absolute;inset:-4px;border-radius:50%;border:2px solid ${color};animation:markerPulse 1.5s infinite;pointer-events:none;"></div>` : ''}
    </div>`;
}

// --- Leaflet CDN loader (idempotent) ----------------------------------------
let _leafletLoading = false;
let _leafletReady = false;
const _listeners = [];

function loadLeaflet() {
  if (_leafletReady) return Promise.resolve();
  return new Promise((resolve, reject) => {
    _listeners.push({ resolve, reject });
    if (_leafletLoading) return;
    _leafletLoading = true;

    const css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(css);

    const js = document.createElement('script');
    js.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    js.onload = () => {
      const heat = document.createElement('script');
      heat.src = 'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js';
      heat.onload = () => {
        _leafletReady = true;
        _listeners.forEach(l => l.resolve());
      };
      heat.onerror = () => {
        // Still resolve — heatmap is optional
        _leafletReady = true;
        _listeners.forEach(l => l.resolve());
      };
      document.head.appendChild(heat);
    };
    js.onerror = () => _listeners.forEach(l => l.reject(new Error('Leaflet load failed')));
    document.head.appendChild(js);
  });
}

// ---------------------------------------------------------------------------
export default function BaseMap({
  markers = [],           // [{ id, lat, lng, type, label, sublabel, meta }]
  triangulate = false,    // draw dashed lines between all markers
  heatmapPoints = [],     // [[lat, lng, intensity], ...]
  userLocation = null,    // [lat, lng]
  centerLat = null,
  centerLng = null,
  zoom = 13,
  height = '100%',
  onMarkerClick = null,
}) {
  const containerRef = useRef(null);
  const mapRef       = useRef(null);
  const markersRef   = useRef([]);
  const linesRef     = useRef([]);
  const heatRef      = useRef(null);
  const userDotRef   = useRef(null);
  const [ready, setReady]       = useState(false);
  const [error, setError]       = useState(false);
  const [popup, setPopup]       = useState(null); // clicked marker

  // --- Init map on mount ---------------------------------------------------
  useEffect(() => {
    let mounted = true;
    loadLeaflet()
      .then(() => {
        if (!mounted || !containerRef.current || mapRef.current) return;
        const L = window.L;

        const lat = centerLat ?? markers.find(m => m.lat)?.lat ?? -1.9441;
        const lng = centerLng ?? markers.find(m => m.lng)?.lng ?? 30.0619;

        const map = L.map(containerRef.current, {
          center: [lat, lng],
          zoom,
          zoomControl: false,
          scrollWheelZoom: true,
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
          maxZoom: 19,
        }).addTo(map);

        L.control.zoom({ position: 'bottomright' }).addTo(map);

        mapRef.current = map;
        if (mounted) setReady(true);
      })
      .catch(() => { if (mounted) setError(true); });

    return () => {
      mounted = false;
      if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; }
    };
  }, []); // eslint-disable-line

  // --- Re-render markers/lines/heatmap whenever data changes ---------------
  useEffect(() => {
    if (!ready || !mapRef.current) return;
    const L   = window.L;
    const map = mapRef.current;

    // Clear previous
    markersRef.current.forEach(m => m.remove());
    linesRef.current.forEach(l => l.remove());
    if (heatRef.current) { map.removeLayer(heatRef.current); heatRef.current = null; }
    if (userDotRef.current) { userDotRef.current.remove(); userDotRef.current = null; }
    markersRef.current = [];
    linesRef.current   = [];

    const valid = markers.filter(m => typeof m.lat === 'number' && typeof m.lng === 'number');

    // Offset markers that share the same coordinates so both are visible
    const posCount = {};
    const spread = valid.map(m => {
      const key = `${m.lat.toFixed(5)},${m.lng.toFixed(5)}`;
      posCount[key] = (posCount[key] || 0) + 1;
      const n = posCount[key];
      return n > 1
        ? { ...m, lat: m.lat + (n - 1) * 0.00015, lng: m.lng + (n - 1) * 0.00015 }
        : m;
    });

    // Add markers
    spread.forEach(m => {
      const color = MARKER_COLORS[m.type] ?? MARKER_COLORS.household;
      const icon  = L.divIcon({
        html: buildPinHtml(color, 34),
        className: '',
        iconSize: [34, 42],
        iconAnchor: [17, 42],
      });
      const lm = L.marker([m.lat, m.lng], { icon })
        .addTo(map)
        .on('click', () => { setPopup(m); onMarkerClick?.(m); });
      markersRef.current.push(lm);
    });

    // Triangulation lines
    if (triangulate && spread.length >= 2) {
      for (let i = 0; i < spread.length; i++) {
        for (let j = i + 1; j < spread.length; j++) {
          const line = L.polyline(
            [[spread[i].lat, spread[i].lng], [spread[j].lat, spread[j].lng]],
            { color: '#eab308', weight: 1.5, opacity: 0.45, dashArray: '6 6' }
          ).addTo(map);
          linesRef.current.push(line);
        }
      }
    }

    // Heatmap
    if (heatmapPoints.length > 0 && window.L?.heatLayer) {
      heatRef.current = window.L.heatLayer(heatmapPoints, {
        radius: 30, blur: 20, maxZoom: 14,
        gradient: { 0.2: '#3b82f6', 0.5: '#eab308', 0.8: '#ef4444', 1.0: '#7f1d1d' },
      }).addTo(map);
    }

    // User location dot
    if (userLocation) {
      const pulseHtml = `
        <div style="position:relative;width:20px;height:20px;">
          <div style="position:absolute;inset:0;border-radius:50%;background:#a855f7;opacity:0.2;animation:userPulse 1.8s infinite;"></div>
          <div style="position:absolute;inset:4px;border-radius:50%;background:#a855f7;border:2.5px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);"></div>
        </div>`;
      userDotRef.current = L.marker(userLocation, {
        icon: L.divIcon({ html: pulseHtml, className: '', iconSize: [20, 20], iconAnchor: [10, 10] }),
        zIndexOffset: 1000,
      }).addTo(map).bindTooltip('📍 You', { permanent: false, direction: 'top', offset: [0, -12] });
    }

    // Fit bounds — guard against zero-area bounds (all markers at same coords)
    if (spread.length > 1) {
      try {
        const bounds = window.L.latLngBounds(spread.map(m => [m.lat, m.lng]));
        const diagonal = bounds.isValid()
          ? bounds.getNorthEast().distanceTo(bounds.getSouthWest())
          : 0;
        if (diagonal > 50) {
          map.fitBounds(bounds, { padding: [60, 60] });
        } else {
          map.setView([spread[0].lat, spread[0].lng], zoom);
        }
      } catch { /* ignore */ }
    } else if (spread.length === 1) {
      map.setView([spread[0].lat, spread[0].lng], zoom);
    }

    map.invalidateSize();
  }, [ready, markers, triangulate, heatmapPoints, userLocation]); // eslint-disable-line

  if (error) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--panel-bg)', borderRadius: 12, border: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        <MapPin size={20} style={{ marginRight: 8 }} /> Map could not be loaded. Check your connection.
      </div>
    );
  }

  // Visible marker types for legend
  const visibleTypes = [...new Set(markers.map(m => m.type))].filter(t => MARKER_COLORS[t]);

  return (
    <div style={{ position: 'relative', height, width: '100%' }}>
      {/* Injected CSS for animations */}
      <style>{`
        @keyframes markerPulse {
          0%,100%{transform:scale(1);opacity:0.6}
          50%{transform:scale(1.8);opacity:0}
        }
        @keyframes userPulse {
          0%,100%{transform:scale(1);opacity:0.2}
          50%{transform:scale(3);opacity:0}
        }
        .leaflet-control-zoom a {
          border-radius: 8px !important;
          border: 1px solid var(--border-color) !important;
          background: var(--panel-bg) !important;
          color: var(--text-main) !important;
          font-weight: 700 !important;
          backdrop-filter: blur(8px) !important;
        }
        .leaflet-control-zoom {
          border: none !important;
          box-shadow: var(--glass-shadow) !important;
          border-radius: 10px !important;
          overflow: hidden;
        }
        .leaflet-attribution-flag { display: none !important; }
        .leaflet-control-attribution {
          background: rgba(15,17,21,0.7) !important;
          color: var(--text-muted) !important;
          font-size: 10px !important;
          backdrop-filter: blur(4px) !important;
        }
        .leaflet-control-attribution a { color: var(--brand-color) !important; }
      `}</style>

      {/* Map container */}
      <div ref={containerRef} style={{ width: '100%', height: '100%', borderRadius: 'inherit' }} />

      {/* Loading overlay */}
      {!ready && !error && (
        <div style={{ position: 'absolute', inset: 0, background: 'var(--panel-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 'inherit', zIndex: 5 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading map…</div>
        </div>
      )}

      {/* Incident count badge */}
      {ready && markers.length > 0 && (
        <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 1000, background: 'var(--brand-color)', color: '#111827', padding: '4px 12px', borderRadius: 20, fontWeight: 700, fontSize: '0.8rem', pointerEvents: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.3)' }}>
          {markers.length} {markers.length === 1 ? 'Location' : 'Locations'}
        </div>
      )}

      {/* Legend */}
      {ready && visibleTypes.length > 0 && (
        <div style={{ position: 'absolute', bottom: 40, left: 12, zIndex: 1000, background: 'rgba(15,17,21,0.88)', backdropFilter: 'blur(12px)', border: '1px solid var(--border-color)', borderRadius: 10, padding: '10px 14px', minWidth: 150, boxShadow: 'var(--glass-shadow)' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.08em', marginBottom: 8 }}>Legend</div>
          {visibleTypes.map(type => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, fontSize: '0.82rem' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: MARKER_COLORS[type], flexShrink: 0 }} />
              <span style={{ color: 'var(--text-main)' }}>{MARKER_LABELS[type] || type}</span>
            </div>
          ))}
          {triangulate && markers.length >= 2 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 5, paddingTop: 5, borderTop: '1px solid var(--border-color)', fontSize: '0.82rem' }}>
              <div style={{ width: 20, borderTop: '1.5px dashed var(--brand-color)', flexShrink: 0, opacity: 0.6 }} />
              <span style={{ color: 'var(--text-muted)' }}>Triangulation</span>
            </div>
          )}
        </div>
      )}

      {/* Click-to-popup overlay */}
      {popup && (
        <div style={{ position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)', zIndex: 2000, width: 280, pointerEvents: 'auto' }}>
          <div className="card animate-slide-in" style={{ padding: 0, overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.6)' }}>
            {/* Header */}
            <div style={{ background: MARKER_COLORS[popup.type] || 'var(--brand-color)', padding: '12px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>{popup.label}</div>
                <div style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.7)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{MARKER_LABELS[popup.type] || popup.type}</div>
              </div>
              <button onClick={() => setPopup(null)} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.8)', cursor: 'pointer', padding: 4 }}>
                <X size={18} />
              </button>
            </div>
            {/* Body */}
            <div style={{ padding: '12px 14px' }}>
              {popup.sublabel && <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 6 }}>{popup.sublabel}</div>}
              {popup.meta && Object.entries(popup.meta).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 6, fontSize: '0.85rem', marginBottom: 4 }}>
                  <span style={{ color: 'var(--text-muted)', textTransform: 'capitalize', minWidth: 70 }}>{k}:</span>
                  <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
