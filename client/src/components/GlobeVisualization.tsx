import React, { useEffect, useMemo, useRef, useState } from 'react';

export interface GlobeEvent {
  lat: number;
  lng: number;
  weight: number;
  type: string;
  title: string;
  description: string;
  date: string;
  location?: string;
  source?: string;
}

interface GlobeVisualizationProps {
  events: GlobeEvent[];
  height?: number;
}

type EventConfig = {
  color: string;
  icon: string;
  label: string;
  glowColor: string;
};

type ViewPoint = {
  lat: number;
  lng: number;
};

type ProjectedEvent = GlobeEvent & {
  x: number;
  y: number;
  depth: number;
  visible: boolean;
};

const BRAZIL_VIEW: ViewPoint = { lat: -14.2, lng: -51.9 };

const EVENT_TYPE_CONFIG: Record<string, EventConfig> = {
  drought: { color: '#f97316', icon: '🌵', label: 'Seca', glowColor: '#f97316' },
  seca: { color: '#f97316', icon: '🌵', label: 'Seca', glowColor: '#f97316' },
  flood: { color: '#3b82f6', icon: '🌊', label: 'Enchente', glowColor: '#3b82f6' },
  enchente: { color: '#3b82f6', icon: '🌊', label: 'Enchente', glowColor: '#3b82f6' },
  inundacao: { color: '#3b82f6', icon: '🌊', label: 'Inundação', glowColor: '#3b82f6' },
  heatwave: { color: '#ef4444', icon: '🔥', label: 'Onda de Calor', glowColor: '#ef4444' },
  onda_calor: { color: '#ef4444', icon: '🔥', label: 'Onda de Calor', glowColor: '#ef4444' },
  incendio: { color: '#ef4444', icon: '🔥', label: 'Incêndio', glowColor: '#ef4444' },
  frost: { color: '#a5f3fc', icon: '❄️', label: 'Geada', glowColor: '#a5f3fc' },
  geada: { color: '#a5f3fc', icon: '❄️', label: 'Geada', glowColor: '#a5f3fc' },
  storm: { color: '#a855f7', icon: '🌪️', label: 'Tempestade', glowColor: '#a855f7' },
  tempestade: { color: '#a855f7', icon: '🌪️', label: 'Tempestade', glowColor: '#a855f7' },
  vendaval: { color: '#a855f7', icon: '🌪️', label: 'Vendaval', glowColor: '#a855f7' },
  granizo: { color: '#67e8f9', icon: '🧊', label: 'Granizo', glowColor: '#67e8f9' },
  landslide: { color: '#92400e', icon: '⛰️', label: 'Deslizamento', glowColor: '#92400e' },
  deslizamento: { color: '#92400e', icon: '⛰️', label: 'Deslizamento', glowColor: '#92400e' },
  default: { color: '#facc15', icon: '⚠️', label: 'Evento', glowColor: '#facc15' },
};

function getEventConfig(type: string) {
  const key = type?.toLowerCase() ?? 'default';
  return EVENT_TYPE_CONFIG[key] ?? EVENT_TYPE_CONFIG.default;
}

function getSeverityLabel(weight: number) {
  if (weight >= 0.8) return { label: 'CRÍTICO', color: '#ef4444', bg: 'rgba(239,68,68,0.15)' };
  if (weight >= 0.6) return { label: 'ALTO', color: '#f97316', bg: 'rgba(249,115,22,0.15)' };
  if (weight >= 0.4) return { label: 'MÉDIO', color: '#eab308', bg: 'rgba(234,179,8,0.15)' };
  return { label: 'BAIXO', color: '#22c55e', bg: 'rgba(34,197,94,0.15)' };
}

function toRadians(value: number) {
  return (value * Math.PI) / 180;
}

function projectPoint(lat: number, lng: number, center: ViewPoint, radius: number) {
  const latRad = toRadians(lat);
  const lngRad = toRadians(lng);
  const centerLat = toRadians(center.lat);
  const centerLng = toRadians(center.lng);
  const deltaLng = lngRad - centerLng;

  const x = radius * Math.cos(latRad) * Math.sin(deltaLng);
  const y = -radius * (
    Math.cos(centerLat) * Math.sin(latRad) -
    Math.sin(centerLat) * Math.cos(latRad) * Math.cos(deltaLng)
  );
  const z =
    Math.sin(centerLat) * Math.sin(latRad) +
    Math.cos(centerLat) * Math.cos(latRad) * Math.cos(deltaLng);

  return { x, y, depth: z, visible: z > 0 };
}

function buildProjectedPath(
  samples: Array<{ lat: number; lng: number }>,
  center: ViewPoint,
  radius: number,
  cx: number,
  cy: number,
) {
  let path = '';
  let drawing = false;

  for (const sample of samples) {
    const point = projectPoint(sample.lat, sample.lng, center, radius);
    if (!point.visible) {
      drawing = false;
      continue;
    }

    const command = drawing ? 'L' : 'M';
    path += `${command}${(cx + point.x).toFixed(2)},${(cy + point.y).toFixed(2)} `;
    drawing = true;
  }

  return path.trim();
}

export function GlobeVisualization({ events, height = 520 }: GlobeVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height });
  const [selectedEvent, setSelectedEvent] = useState<GlobeEvent | null>(null);
  const [showSidebar, setShowSidebar] = useState(false);
  const [filterType, setFilterType] = useState<string | null>(null);
  const [viewPoint, setViewPoint] = useState<ViewPoint>(BRAZIL_VIEW);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({ width: containerRef.current.offsetWidth, height });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [height]);

  const radius = useMemo(
    () => Math.max(120, Math.min(dimensions.width * 0.28, height * 0.38)),
    [dimensions.width, height],
  );
  const centerX = dimensions.width / 2;
  const centerY = height / 2 + 8;

  const projectedEvents = useMemo<ProjectedEvent[]>(() => {
    return events
      .map((event) => ({
        ...event,
        ...projectPoint(event.lat, event.lng, viewPoint, radius),
      }))
      .sort((left, right) => left.depth - right.depth);
  }, [events, radius, viewPoint]);

  const visibleEvents = useMemo(() => projectedEvents.filter((event) => event.visible), [projectedEvents]);

  const presentTypes = useMemo(
    () => Array.from(new Set(events.map((event) => event.type.toLowerCase())))
      .map((key) => ({ key, cfg: getEventConfig(key) }))
      .slice(0, 8),
    [events],
  );

  const sidebarEvents = useMemo(
    () => (filterType ? events.filter((event) => event.type.toLowerCase() === filterType) : events),
    [events, filterType],
  );

  const topSeverityEvents = useMemo(
    () => [...events].sort((left, right) => right.weight - left.weight).slice(0, 4),
    [events],
  );

  const arcs = useMemo(() => {
    if (topSeverityEvents.length < 2) {
      return [] as string[];
    }

    const paths: string[] = [];
    for (let index = 0; index < topSeverityEvents.length - 1; index += 1) {
      const start = visibleEvents.find((event) => event.title === topSeverityEvents[index].title);
      const end = visibleEvents.find((event) => event.title === topSeverityEvents[index + 1].title);
      if (!start || !end) {
        continue;
      }

      const controlX = (centerX + start.x + centerX + end.x) / 2;
      const controlY = Math.min(centerY + start.y, centerY + end.y) - 42;
      paths.push(`M ${centerX + start.x} ${centerY + start.y} Q ${controlX} ${controlY} ${centerX + end.x} ${centerY + end.y}`);
    }

    return paths;
  }, [centerX, centerY, topSeverityEvents, visibleEvents]);

  const graticulePaths = useMemo(() => {
    const latitudeLines = [-60, -30, 0, 30, 60].map((lat) => {
      const samples = Array.from({ length: 181 }, (_, index) => ({ lat, lng: index * 2 - 180 }));
      return buildProjectedPath(samples, viewPoint, radius, centerX, centerY);
    });

    const longitudeLines = [-120, -90, -60, -30, 0, 30, 60, 90, 120].map((lng) => {
      const samples = Array.from({ length: 121 }, (_, index) => ({ lat: index * 1.5 - 90, lng }));
      return buildProjectedPath(samples, viewPoint, radius, centerX, centerY);
    });

    return [...latitudeLines, ...longitudeLines].filter(Boolean);
  }, [centerX, centerY, radius, viewPoint]);

  const selectedCfg = selectedEvent ? getEventConfig(selectedEvent.type) : null;
  const selectedSev = selectedEvent ? getSeverityLabel(selectedEvent.weight) : null;

  const handleSelectEvent = (event: GlobeEvent) => {
    setSelectedEvent((previous) => {
      const shouldClose = previous && previous.lat === event.lat && previous.lng === event.lng && previous.title === event.title;
      if (shouldClose) {
        return null;
      }

      setViewPoint({ lat: event.lat, lng: event.lng });
      return event;
    });
  };

  const resetToBrazil = () => {
    setSelectedEvent(null);
    setViewPoint(BRAZIL_VIEW);
  };

  if (!dimensions.width) {
    return (
      <div
        ref={containerRef}
        style={{ height }}
        className="w-full flex items-center justify-center bg-slate-950 rounded-2xl border border-slate-800"
      >
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-sm">Preparando visualizacao de eventos...</span>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="w-full rounded-2xl overflow-hidden relative"
      style={{
        height,
        background: 'linear-gradient(135deg, #020617 0%, #0a0f23 50%, #020617 100%)',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        boxShadow: '0 0 60px rgba(99, 102, 241, 0.08), 0 25px 50px rgba(0,0,0,0.6)',
      }}
    >
      <div style={{ position: 'absolute', top: 16, left: 16, right: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 20 }}>
        <div style={{ background: 'rgba(0,0,0,0.65)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '10px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '10px', backdropFilter: 'blur(8px)' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444', display: 'inline-block', boxShadow: '0 0 8px #ef4444', animation: 'pulse-dot 1.5s ease-in-out infinite' }} />
          <span style={{ color: '#f1f5f9', fontSize: 11, fontWeight: 700, letterSpacing: '0.1em' }}>EVENTOS CLIMÁTICOS • LIVE</span>
          <span style={{ background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '999px', padding: '1px 8px', color: '#ef4444', fontSize: 11, fontWeight: 700 }}>{events.length}</span>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={resetToBrazil} style={{ background: 'rgba(0,0,0,0.65)', border: '1px solid rgba(34,197,94,0.4)', borderRadius: '10px', padding: '6px 12px', color: '#4ade80', fontSize: 10, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, backdropFilter: 'blur(8px)' }}>🇧🇷 Brasil</button>
          <button onClick={() => setShowSidebar((value) => !value)} style={{ background: showSidebar ? 'rgba(99,102,241,0.3)' : 'rgba(0,0,0,0.65)', border: `1px solid ${showSidebar ? 'rgba(99,102,241,0.6)' : 'rgba(255,255,255,0.1)'}`, borderRadius: '10px', padding: '6px 12px', color: '#e2e8f0', fontSize: 10, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, backdropFilter: 'blur(8px)' }}>📋 Lista</button>
          <div style={{ background: 'rgba(0,0,0,0.65)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '12px', backdropFilter: 'blur(8px)' }}>
            {[
              { label: 'Crítico', color: '#ef4444' },
              { label: 'Alto', color: '#f97316' },
              { label: 'Médio', color: '#eab308' },
              { label: 'Baixo', color: '#22c55e' },
            ].map((item) => (
              <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: item.color, boxShadow: `0 0 6px ${item.color}`, display: 'inline-block' }} />
                <span style={{ color: '#94a3b8', fontSize: 10, fontWeight: 600 }}>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {showSidebar && (
        <div style={{ position: 'absolute', top: 56, right: 16, bottom: 16, width: 280, zIndex: 25, background: 'rgba(2,6,23,0.92)', backdropFilter: 'blur(12px)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '14px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '12px 14px 8px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ color: '#f1f5f9', fontSize: 12, fontWeight: 700, marginBottom: 8 }}>Todos os Eventos ({sidebarEvents.length})</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              <button onClick={() => setFilterType(null)} style={{ background: filterType === null ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.05)', border: `1px solid ${filterType === null ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.1)'}`, borderRadius: 6, padding: '2px 8px', color: '#e2e8f0', fontSize: 9, fontWeight: 600, cursor: 'pointer' }}>Todos</button>
              {presentTypes.map(({ key, cfg }) => (
                <button key={key} onClick={() => setFilterType((value) => (value === key ? null : key))} style={{ background: filterType === key ? `${cfg.color}33` : 'rgba(255,255,255,0.05)', border: `1px solid ${filterType === key ? `${cfg.color}66` : 'rgba(255,255,255,0.1)'}`, borderRadius: 6, padding: '2px 8px', color: filterType === key ? cfg.color : '#94a3b8', fontSize: 9, fontWeight: 600, cursor: 'pointer' }}>{cfg.icon} {cfg.label}</button>
              ))}
            </div>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '8px 10px' }}>
            {sidebarEvents.slice().sort((left, right) => right.weight - left.weight).map((event, index) => {
              const cfg = getEventConfig(event.type);
              const sev = getSeverityLabel(event.weight);
              const isSelected = selectedEvent?.title === event.title && selectedEvent?.lat === event.lat;
              return (
                <div key={`${event.lat}-${event.lng}-${index}`} onClick={() => handleSelectEvent(event)} style={{ padding: '8px 10px', marginBottom: 6, background: isSelected ? `${cfg.color}18` : 'rgba(255,255,255,0.03)', border: `1px solid ${isSelected ? `${cfg.color}55` : 'rgba(255,255,255,0.06)'}`, borderRadius: 10, cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 16 }}>{cfg.icon}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ color: '#e2e8f0', fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{event.location || event.title || cfg.label}</div>
                      <div style={{ color: '#64748b', fontSize: 9, marginTop: 1 }}>{event.date ? new Date(event.date).toLocaleDateString('pt-BR') : ''}{event.source ? ` • ${event.source}` : ''}</div>
                    </div>
                    <div style={{ background: sev.bg, border: `1px solid ${sev.color}44`, borderRadius: 6, padding: '2px 6px', color: sev.color, fontSize: 9, fontWeight: 700 }}>{(event.weight * 10).toFixed(1)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {selectedEvent && selectedCfg && selectedSev && (
        <div style={{ position: 'absolute', bottom: 16, left: 16, zIndex: 25, width: 320, maxWidth: 'calc(100% - 32px)', background: 'rgba(2,6,23,0.94)', backdropFilter: 'blur(14px)', border: `1px solid ${selectedCfg.color}44`, borderRadius: '16px', overflow: 'hidden', boxShadow: `0 20px 40px rgba(0,0,0,0.6), 0 0 30px ${selectedCfg.glowColor}15`, animation: 'slideUp 0.3s ease' }}>
          <div style={{ background: `linear-gradient(135deg, ${selectedCfg.color}22, transparent)`, padding: '14px 16px 10px', borderBottom: `1px solid ${selectedCfg.color}22`, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
            <span style={{ fontSize: 28 }}>{selectedCfg.icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 800, lineHeight: 1.3 }}>{selectedEvent.title || selectedCfg.label}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                <span style={{ background: selectedSev.bg, border: `1px solid ${selectedSev.color}55`, borderRadius: 6, padding: '2px 8px', color: selectedSev.color, fontSize: 10, fontWeight: 700 }}>● {selectedSev.label}</span>
                <span style={{ background: `${selectedCfg.color}22`, border: `1px solid ${selectedCfg.color}55`, borderRadius: 6, padding: '2px 8px', color: selectedCfg.color, fontSize: 10, fontWeight: 700 }}>{selectedCfg.label}</span>
              </div>
            </div>
            <button onClick={() => setSelectedEvent(null)} style={{ background: 'rgba(255,255,255,0.08)', border: 'none', borderRadius: 8, width: 28, height: 28, color: '#94a3b8', fontSize: 14, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>✕</button>
          </div>
          <div style={{ padding: '12px 16px' }}>
            {selectedEvent.description && <div style={{ color: '#cbd5e1', fontSize: 11, lineHeight: 1.5, marginBottom: 12, paddingBottom: 10, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{selectedEvent.description}</div>}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px' }}>
              <div><div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 2 }}>LOCALIZAÇÃO</div><div style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600 }}>{selectedEvent.location || 'N/A'}</div></div>
              <div><div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 2 }}>SEVERIDADE</div><div style={{ color: selectedSev.color, fontSize: 18, fontWeight: 800 }}>{(selectedEvent.weight * 10).toFixed(1)}<span style={{ fontSize: 10, color: '#64748b', fontWeight: 500 }}> / 10</span></div></div>
              <div><div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 2 }}>DATA</div><div style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600 }}>{selectedEvent.date ? new Date(selectedEvent.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : 'N/A'}</div></div>
              <div><div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 2 }}>COORDENADAS</div><div style={{ color: '#94a3b8', fontSize: 10, fontFamily: 'monospace' }}>{selectedEvent.lat.toFixed(3)}°, {selectedEvent.lng.toFixed(3)}°</div></div>
            </div>
            {selectedEvent.source && <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.06)', color: '#64748b', fontSize: 9 }}>Fonte: <span style={{ color: '#94a3b8', fontWeight: 600 }}>{selectedEvent.source}</span></div>}
            <div style={{ marginTop: 10 }}><div style={{ width: '100%', height: 4, borderRadius: 4, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}><div style={{ width: `${selectedEvent.weight * 100}%`, height: '100%', borderRadius: 4, background: `linear-gradient(90deg, ${selectedSev.color}88, ${selectedSev.color})` }} /></div></div>
          </div>
        </div>
      )}

      {!selectedEvent && presentTypes.length > 0 && (
        <div style={{ position: 'absolute', bottom: 16, left: 16, zIndex: 20, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={{ color: '#64748b', fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', marginBottom: 2 }}>TIPOS DE EVENTO</span>
          {presentTypes.map(({ key, cfg }) => (
            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ fontSize: 13 }}>{cfg.icon}</span><span style={{ color: cfg.color, fontSize: 10, fontWeight: 600 }}>{cfg.label}</span></div>
          ))}
        </div>
      )}

      {!showSidebar && (
        <div style={{ position: 'absolute', bottom: 16, right: 16, zIndex: 20, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', padding: '10px 16px', display: 'flex', flexDirection: 'column', gap: 4, textAlign: 'right' }}>
          <span style={{ color: '#64748b', fontSize: 9, fontWeight: 700, letterSpacing: '0.1em' }}>TOP SEVERIDADE</span>
          {[...events].sort((left, right) => right.weight - left.weight).slice(0, 3).map((event, index) => {
            const cfg = getEventConfig(event.type);
            return <div key={`${event.title}-${index}`} onClick={() => handleSelectEvent(event)} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', padding: '2px 0' }}><span style={{ fontSize: 11 }}>{cfg.icon}</span><span style={{ color: '#e2e8f0', fontSize: 10, fontWeight: 600 }}>{(event.weight * 10).toFixed(1)}</span><span style={{ color: cfg.color, fontSize: 9 }}>{cfg.label}</span></div>;
          })}
        </div>
      )}

      <svg width={dimensions.width} height={height} style={{ display: 'block' }}>
        <defs>
          <radialGradient id="globeFill" cx="38%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#17335d" />
            <stop offset="45%" stopColor="#0f2747" />
            <stop offset="100%" stopColor="#071224" />
          </radialGradient>
          <radialGradient id="globeGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(59,130,246,0.35)" />
            <stop offset="100%" stopColor="rgba(2,6,23,0)" />
          </radialGradient>
          <clipPath id="globeClip"><circle cx={centerX} cy={centerY} r={radius} /></clipPath>
        </defs>

        <circle cx={centerX} cy={centerY} r={radius + 22} fill="url(#globeGlow)" />
        <circle cx={centerX} cy={centerY} r={radius} fill="url(#globeFill)" stroke="rgba(148,163,184,0.18)" strokeWidth="1.2" />
        <ellipse cx={centerX - radius * 0.18} cy={centerY - radius * 0.22} rx={radius * 0.18} ry={radius * 0.42} fill="rgba(255,255,255,0.08)" />

        <g clipPath="url(#globeClip)">
          {graticulePaths.map((path, index) => <path key={`grid-${index}`} d={path} fill="none" stroke="rgba(148,163,184,0.18)" strokeWidth="0.9" />)}
          {arcs.map((path, index) => <path key={`arc-${index}`} d={path} fill="none" stroke="rgba(99,102,241,0.35)" strokeWidth="1.2" strokeDasharray="5 7" />)}
        </g>

        {visibleEvents.map((event) => {
          const cfg = getEventConfig(event.type);
          const markerRadius = 4 + event.weight * 6;
          const x = centerX + event.x;
          const y = centerY + event.y;
          return (
            <g key={`${event.lat}-${event.lng}-${event.title}`} style={{ cursor: 'pointer' }} onClick={() => handleSelectEvent(event)}>
              <circle cx={x} cy={y} r={markerRadius + 5} fill={`${cfg.color}22`} />
              <circle cx={x} cy={y} r={markerRadius} fill={cfg.color} stroke="rgba(255,255,255,0.65)" strokeWidth="1.2" />
            </g>
          );
        })}
      </svg>

      {visibleEvents.map((event, index) => {
        const cfg = getEventConfig(event.type);
        const sev = getSeverityLabel(event.weight);
        const x = centerX + event.x;
        const y = centerY + event.y;
        const isSelected = selectedEvent?.title === event.title && selectedEvent?.lat === event.lat;
        return (
          <button key={`label-${event.lat}-${event.lng}-${index}`} type="button" onClick={() => handleSelectEvent(event)} style={{ position: 'absolute', left: x, top: y, transform: 'translate(-50%, -110%)', zIndex: isSelected ? 22 : 12, background: 'rgba(15,23,42,0.92)', border: `1px solid ${isSelected ? `${cfg.color}bb` : `${cfg.color}66`}`, borderRadius: 10, padding: '6px 10px', minWidth: 84, maxWidth: 150, boxShadow: `0 8px 20px rgba(0,0,0,0.5), 0 0 12px ${cfg.glowColor}22`, backdropFilter: 'blur(8px)', color: '#f8fafc', cursor: 'pointer', textAlign: 'left' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 14, lineHeight: 1 }}>{cfg.icon}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: 'white', fontSize: 10, fontWeight: 700, letterSpacing: '0.02em', lineHeight: 1.2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{event.location || cfg.label}</div>
                <div style={{ color: sev.color, fontSize: 9, fontWeight: 600 }}>● {sev.label}</div>
              </div>
              <div style={{ background: `${cfg.color}22`, border: `1px solid ${cfg.color}55`, borderRadius: 999, padding: '1px 5px', fontSize: 9, fontWeight: 700, color: cfg.color, flexShrink: 0 }}>{(event.weight * 10).toFixed(1)}</div>
            </div>
          </button>
        );
      })}

      <style>{`
        @keyframes pulse-dot {
          0%,100% { opacity:1; transform:scale(1); }
          50% { opacity:0.6; transform:scale(1.4); }
        }
        @keyframes slideUp {
          from { opacity:0; transform:translateY(16px); }
          to { opacity:1; transform:translateY(0); }
        }
        div::-webkit-scrollbar { width:4px; }
        div::-webkit-scrollbar-track { background:transparent; }
        div::-webkit-scrollbar-thumb { background:rgba(99,102,241,0.3); border-radius:4px; }
      `}</style>
    </div>
  );
}
