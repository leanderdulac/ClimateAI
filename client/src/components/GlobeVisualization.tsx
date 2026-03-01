import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import Globe, { GlobeMethods } from 'react-globe.gl';

export interface GlobeEvent {
    lat: number;
    lng: number;
    weight: number; // 0 to 1, representing severity
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

// Per-event-type config: color, icon (emoji), label, glow color
const EVENT_TYPE_CONFIG: Record<string, { color: string; ringColor: string; icon: string; label: string; glowColor: string }> = {
    drought: { color: '#f97316', ringColor: 'rgba(249, 115, 22, ', icon: '🌵', label: 'Seca', glowColor: '#f97316' },
    seca: { color: '#f97316', ringColor: 'rgba(249, 115, 22, ', icon: '🌵', label: 'Seca', glowColor: '#f97316' },
    flood: { color: '#3b82f6', ringColor: 'rgba(59, 130, 246, ', icon: '🌊', label: 'Enchente', glowColor: '#3b82f6' },
    enchente: { color: '#3b82f6', ringColor: 'rgba(59, 130, 246, ', icon: '🌊', label: 'Enchente', glowColor: '#3b82f6' },
    inundacao: { color: '#3b82f6', ringColor: 'rgba(59, 130, 246, ', icon: '🌊', label: 'Inundação', glowColor: '#3b82f6' },
    heatwave: { color: '#ef4444', ringColor: 'rgba(239, 68, 68, ', icon: '🔥', label: 'Onda de Calor', glowColor: '#ef4444' },
    onda_calor: { color: '#ef4444', ringColor: 'rgba(239, 68, 68, ', icon: '🔥', label: 'Onda de Calor', glowColor: '#ef4444' },
    incendio: { color: '#ef4444', ringColor: 'rgba(239, 68, 68, ', icon: '🔥', label: 'Incêndio', glowColor: '#ef4444' },
    frost: { color: '#a5f3fc', ringColor: 'rgba(165, 243, 252, ', icon: '❄️', label: 'Geada', glowColor: '#a5f3fc' },
    geada: { color: '#a5f3fc', ringColor: 'rgba(165, 243, 252, ', icon: '❄️', label: 'Geada', glowColor: '#a5f3fc' },
    storm: { color: '#a855f7', ringColor: 'rgba(168, 85, 247, ', icon: '🌪️', label: 'Tempestade', glowColor: '#a855f7' },
    tempestade: { color: '#a855f7', ringColor: 'rgba(168, 85, 247, ', icon: '🌪️', label: 'Tempestade', glowColor: '#a855f7' },
    vendaval: { color: '#a855f7', ringColor: 'rgba(168, 85, 247, ', icon: '🌪️', label: 'Vendaval', glowColor: '#a855f7' },
    granizo: { color: '#67e8f9', ringColor: 'rgba(103, 232, 249, ', icon: '🧊', label: 'Granizo', glowColor: '#67e8f9' },
    landslide: { color: '#92400e', ringColor: 'rgba(146, 64, 14, ', icon: '⛰️', label: 'Deslizamento', glowColor: '#92400e' },
    deslizamento: { color: '#92400e', ringColor: 'rgba(146, 64, 14, ', icon: '⛰️', label: 'Deslizamento', glowColor: '#92400e' },
    default: { color: '#facc15', ringColor: 'rgba(250, 204, 21, ', icon: '⚠️', label: 'Evento', glowColor: '#facc15' },
};

function getEventConfig(type: string) {
    const key = type?.toLowerCase() ?? 'default';
    return EVENT_TYPE_CONFIG[key] ?? EVENT_TYPE_CONFIG['default'];
}

function getSeverityLabel(weight: number) {
    if (weight >= 0.8) return { label: 'CRÍTICO', color: '#ef4444', bg: 'rgba(239,68,68,0.15)' };
    if (weight >= 0.6) return { label: 'ALTO', color: '#f97316', bg: 'rgba(249,115,22,0.15)' };
    if (weight >= 0.4) return { label: 'MÉDIO', color: '#eab308', bg: 'rgba(234,179,8,0.15)' };
    return { label: 'BAIXO', color: '#22c55e', bg: 'rgba(34,197,94,0.15)' };
}

export function GlobeVisualization({ events, height = 520 }: GlobeVisualizationProps) {
    const globeEl = useRef<GlobeMethods>();
    const [dimensions, setDimensions] = useState({ width: 0, height });
    const containerRef = useRef<HTMLDivElement>(null);
    const [selectedEvent, setSelectedEvent] = useState<GlobeEvent | null>(null);
    const [showSidebar, setShowSidebar] = useState(false);
    const [filterType, setFilterType] = useState<string | null>(null);
    const globeReady = useRef(false);

    // Brazil center coordinates
    const BRAZIL_VIEW = { lat: -14.2, lng: -51.9, altitude: 1.8 };

    // Build ring data for pulsing markers
    const ringsData = useMemo(() => {
        return events.map((event, idx) => {
            const cfg = getEventConfig(event.type);
            const severity = event.weight;
            return {
                ...event,
                idx,
                maxR: severity * 6 + 2,
                propagationSpeed: 1.5 + severity * 1.5,
                repeatPeriod: 600 + (1 - severity) * 800,
                color: cfg.ringColor,
            };
        });
    }, [events]);

    // Arcs between the top-N highest-severity events (visual connection)
    const arcsData = useMemo(() => {
        if (events.length < 2) return [];
        const sorted = [...events].sort((a, b) => b.weight - a.weight).slice(0, 4);
        const arcs = [];
        for (let i = 0; i < sorted.length - 1; i++) {
            const cfgSrc = getEventConfig(sorted[i].type);
            arcs.push({
                startLat: sorted[i].lat,
                startLng: sorted[i].lng,
                endLat: sorted[i + 1].lat,
                endLng: sorted[i + 1].lng,
                color: [cfgSrc.color + 'cc', getEventConfig(sorted[i + 1].type).color + 'cc'],
                stroke: 0.8,
            });
        }
        return arcs;
    }, [events]);

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

    useEffect(() => {
        if (globeEl.current) {
            const controls = globeEl.current.controls();
            controls.autoRotate = false;
            controls.enableDamping = true;
            controls.dampingFactor = 0.12;
            controls.minDistance = 120;  // allow deep zoom into localities
            controls.maxDistance = 520;
            controls.rotateSpeed = 0.5;
            controls.zoomSpeed = 1.2;

            // Center on Brazil on first render
            if (!globeReady.current) {
                globeReady.current = true;
                globeEl.current.pointOfView(BRAZIL_VIEW, 0);
            }
        }
    }, [dimensions]);

    const resetToBrazil = useCallback(() => {
        if (globeEl.current) {
            setSelectedEvent(null);
            globeEl.current.pointOfView(BRAZIL_VIEW, 1200);
        }
    }, []);

    // Fly to event on selection
    const flyToEvent = useCallback((event: GlobeEvent) => {
        if (globeEl.current) {
            globeEl.current.pointOfView(
                { lat: event.lat, lng: event.lng, altitude: 0.8 },
                1200
            );
        }
    }, []);

    const handleSelectEvent = useCallback((event: GlobeEvent) => {
        setSelectedEvent(prev => {
            if (prev && prev.lat === event.lat && prev.lng === event.lng && prev.title === event.title) {
                return null;
            }
            flyToEvent(event);
            return event;
        });
    }, [flyToEvent]);

    const handleMouseLeave = useCallback(() => {
        // Globe is static, no action needed
    }, []);

    // Build HTML marker elements per event — minimal on globe, detail in panel
    const buildMarker = useCallback((d: any) => {
        const cfg = getEventConfig(d.type);
        const sev = getSeverityLabel(d.weight);
        const el = document.createElement('div');
        el.style.cssText = 'cursor:pointer;pointer-events:auto;';

        el.innerHTML = `
            <div style="
                display:flex;flex-direction:column;align-items:center;
                transform:translate(-50%,-100%);
                transition:transform 0.25s cubic-bezier(0.34,1.56,0.64,1);
            " class="globe-pin" data-idx="${d.idx}">
                <!-- Compact label -->
                <div class="globe-marker-card" style="
                    background:rgba(15,23,42,0.92);
                    border:1px solid ${cfg.color}66;
                    border-radius:10px;
                    padding:6px 10px;
                    min-width:80px;
                    max-width:140px;
                    box-shadow:0 8px 20px rgba(0,0,0,0.5), 0 0 12px ${cfg.glowColor}22;
                    transition:all 0.25s ease;
                    backdrop-filter:blur(8px);
                ">
                    <div style="display:flex;align-items:center;gap:6px;">
                        <span style="font-size:14px;line-height:1;">${cfg.icon}</span>
                        <div style="flex:1;min-width:0;">
                            <div style="color:white;font-size:10px;font-weight:700;letter-spacing:0.02em;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                ${d.location || cfg.label}
                            </div>
                            <div style="color:${sev.color};font-size:9px;font-weight:600;">● ${sev.label}</div>
                        </div>
                        <div style="
                            background:${cfg.color}22;
                            border:1px solid ${cfg.color}55;
                            border-radius:999px;
                            padding:1px 5px;
                            font-size:9px;
                            font-weight:700;
                            color:${cfg.color};
                            flex-shrink:0;
                        ">${(d.weight * 10).toFixed(1)}</div>
                    </div>
                </div>
                <!-- Connector -->
                <div style="width:1.5px;height:18px;background:linear-gradient(to bottom,${cfg.color}cc,transparent);"></div>
                <!-- Pin dot -->
                <div style="
                    width:8px;height:8px;border-radius:50%;
                    background:${cfg.color};
                    box-shadow:0 0 10px ${cfg.glowColor};
                    animation:pulse-dot 2s ease-in-out infinite;
                    flex-shrink:0;
                "></div>
            </div>
        `;

        // Click → select + fly
        el.onclick = (e) => {
            e.stopPropagation();
            handleSelectEvent(d as GlobeEvent);
        };

        // Hover effects
        el.onmouseenter = () => {
            setIsAutoRotating(false);
            const card = el.querySelector('.globe-marker-card') as HTMLElement;
            if (card) {
                card.style.borderColor = cfg.color + 'bb';
                card.style.boxShadow = `0 8px 25px rgba(0,0,0,0.6), 0 0 20px ${cfg.glowColor}44`;
                card.style.transform = 'scale(1.08)';
            }
        };
        el.onmouseleave = () => {
            // static globe — nothing to resume
            const card = el.querySelector('.globe-marker-card') as HTMLElement;
            if (card) {
                card.style.borderColor = cfg.color + '66';
                card.style.boxShadow = `0 8px 20px rgba(0,0,0,0.5), 0 0 12px ${cfg.glowColor}22`;
                card.style.transform = 'scale(1)';
            }
        };

        return el;
    }, [handleSelectEvent, selectedEvent]);

    if (!dimensions.width) {
        return (
            <div
                ref={containerRef}
                style={{ height }}
                className="w-full flex items-center justify-center bg-slate-950 rounded-2xl border border-slate-800"
            >
                <div className="flex flex-col items-center gap-3 text-slate-500">
                    <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
                    <span className="text-sm">Carregando globo 3D...</span>
                </div>
            </div>
        );
    }

    // Unique event types for legend
    const presentTypes = Array.from(new Set(events.map(e => e.type.toLowerCase())))
        .map(t => ({ key: t, cfg: getEventConfig(t) }))
        .slice(0, 8);

    // Filtered events for sidebar
    const sidebarEvents = filterType
        ? events.filter(e => e.type.toLowerCase() === filterType)
        : events;

    const selectedCfg = selectedEvent ? getEventConfig(selectedEvent.type) : null;
    const selectedSev = selectedEvent ? getSeverityLabel(selectedEvent.weight) : null;

    return (
        <div
            ref={containerRef}
            className="w-full rounded-2xl overflow-hidden relative"
            style={{
                background: 'linear-gradient(135deg, #020617 0%, #0a0f23 50%, #020617 100%)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                boxShadow: '0 0 60px rgba(99, 102, 241, 0.08), 0 25px 50px rgba(0,0,0,0.6)',
            }}
            onMouseLeave={handleMouseLeave}
        >
            {/* Top status bar */}
            <div style={{
                position: 'absolute', top: 16, left: 16, right: 16,
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 20,
            }}>
                <div style={{
                    background: 'rgba(0,0,0,0.65)',
                    border: '1px solid rgba(239,68,68,0.4)',
                    borderRadius: '10px',
                    padding: '6px 14px',
                    display: 'flex', alignItems: 'center', gap: '10px',
                    backdropFilter: 'blur(8px)',
                }}>
                    <span style={{
                        width: 8, height: 8, borderRadius: '50%',
                        background: '#ef4444',
                        display: 'inline-block',
                        boxShadow: '0 0 8px #ef4444',
                        animation: 'pulse-dot 1.5s ease-in-out infinite',
                    }} />
                    <span style={{ color: '#f1f5f9', fontSize: 11, fontWeight: 700, letterSpacing: '0.1em' }}>
                        EVENTOS CLIMÁTICOS • LIVE
                    </span>
                    <span style={{
                        background: 'rgba(239,68,68,0.2)',
                        border: '1px solid rgba(239,68,68,0.4)',
                        borderRadius: '999px',
                        padding: '1px 8px',
                        color: '#ef4444',
                        fontSize: 11,
                        fontWeight: 700,
                    }}>
                        {events.length}
                    </span>
                </div>

                {/* Controls */}
                <div style={{ display: 'flex', gap: 8 }}>
                    {/* Reset to Brazil view */}
                    <button
                        onClick={resetToBrazil}
                        style={{
                            background: 'rgba(0,0,0,0.65)',
                            border: '1px solid rgba(34,197,94,0.4)',
                            borderRadius: '10px', padding: '6px 12px',
                            color: '#4ade80', fontSize: 10, fontWeight: 600,
                            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
                            backdropFilter: 'blur(8px)', transition: 'all 0.2s ease',
                        }}
                    >
                        🇧🇷 Brasil
                    </button>
                    {/* Toggle event list sidebar */}
                    <button
                        onClick={() => setShowSidebar(!showSidebar)}
                        style={{
                            background: showSidebar ? 'rgba(99,102,241,0.3)' : 'rgba(0,0,0,0.65)',
                            border: `1px solid ${showSidebar ? 'rgba(99,102,241,0.6)' : 'rgba(255,255,255,0.1)'}`,
                            borderRadius: '10px', padding: '6px 12px',
                            color: '#e2e8f0', fontSize: 10, fontWeight: 600,
                            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
                            backdropFilter: 'blur(8px)', transition: 'all 0.2s ease',
                        }}
                    >
                        📋 Lista
                    </button>
                    {/* Severity legend */}
                    <div style={{
                        background: 'rgba(0,0,0,0.65)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '10px', padding: '6px 12px',
                        display: 'flex', alignItems: 'center', gap: '12px',
                        backdropFilter: 'blur(8px)',
                    }}>
                        {[
                            { label: 'Crítico', color: '#ef4444' },
                            { label: 'Alto', color: '#f97316' },
                            { label: 'Médio', color: '#eab308' },
                            { label: 'Baixo', color: '#22c55e' },
                        ].map(s => (
                            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.color, boxShadow: `0 0 6px ${s.color}`, display: 'inline-block' }} />
                                <span style={{ color: '#94a3b8', fontSize: 10, fontWeight: 600 }}>{s.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Event List Sidebar ── */}
            {showSidebar && (
                <div style={{
                    position: 'absolute', top: 56, right: 16, bottom: 16, width: 280, zIndex: 25,
                    background: 'rgba(2,6,23,0.92)', backdropFilter: 'blur(12px)',
                    border: '1px solid rgba(99,102,241,0.2)', borderRadius: '14px',
                    display: 'flex', flexDirection: 'column', overflow: 'hidden',
                }}>
                    {/* Sidebar header */}
                    <div style={{
                        padding: '12px 14px 8px', borderBottom: '1px solid rgba(255,255,255,0.08)',
                    }}>
                        <div style={{ color: '#f1f5f9', fontSize: 12, fontWeight: 700, marginBottom: 8 }}>
                            Todos os Eventos ({sidebarEvents.length})
                        </div>
                        {/* Type filter chips */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            <button
                                onClick={() => setFilterType(null)}
                                style={{
                                    background: filterType === null ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.05)',
                                    border: `1px solid ${filterType === null ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.1)'}`,
                                    borderRadius: 6, padding: '2px 8px',
                                    color: '#e2e8f0', fontSize: 9, fontWeight: 600, cursor: 'pointer',
                                }}
                            >Todos</button>
                            {presentTypes.map(({ key, cfg }) => (
                                <button
                                    key={key}
                                    onClick={() => setFilterType(filterType === key ? null : key)}
                                    style={{
                                        background: filterType === key ? cfg.color + '33' : 'rgba(255,255,255,0.05)',
                                        border: `1px solid ${filterType === key ? cfg.color + '66' : 'rgba(255,255,255,0.1)'}`,
                                        borderRadius: 6, padding: '2px 8px',
                                        color: filterType === key ? cfg.color : '#94a3b8',
                                        fontSize: 9, fontWeight: 600, cursor: 'pointer',
                                    }}
                                >{cfg.icon} {cfg.label}</button>
                            ))}
                        </div>
                    </div>
                    {/* Scrollable event list */}
                    <div style={{ flex: 1, overflowY: 'auto', padding: '8px 10px' }}>
                        {sidebarEvents.sort((a, b) => b.weight - a.weight).map((event, idx) => {
                            const cfg = getEventConfig(event.type);
                            const sev = getSeverityLabel(event.weight);
                            const isSelected = selectedEvent?.title === event.title && selectedEvent?.lat === event.lat;
                            return (
                                <div
                                    key={`${event.lat}-${event.lng}-${idx}`}
                                    onClick={() => handleSelectEvent(event)}
                                    style={{
                                        padding: '8px 10px', marginBottom: 6,
                                        background: isSelected ? cfg.color + '18' : 'rgba(255,255,255,0.03)',
                                        border: `1px solid ${isSelected ? cfg.color + '55' : 'rgba(255,255,255,0.06)'}`,
                                        borderRadius: 10, cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                    }}
                                    onMouseEnter={(e) => {
                                        (e.currentTarget as HTMLElement).style.background = cfg.color + '12';
                                        (e.currentTarget as HTMLElement).style.borderColor = cfg.color + '44';
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!isSelected) {
                                            (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.03)';
                                            (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.06)';
                                        }
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span style={{ fontSize: 16 }}>{cfg.icon}</span>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{
                                                color: '#e2e8f0', fontSize: 10, fontWeight: 700,
                                                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                            }}>{event.location || event.title || cfg.label}</div>
                                            <div style={{ color: '#64748b', fontSize: 9, marginTop: 1 }}>
                                                {event.date ? new Date(event.date).toLocaleDateString('pt-BR') : ''}
                                                {event.source ? ` • ${event.source}` : ''}
                                            </div>
                                        </div>
                                        <div style={{
                                            background: sev.bg, border: `1px solid ${sev.color}44`,
                                            borderRadius: 6, padding: '2px 6px',
                                            color: sev.color, fontSize: 9, fontWeight: 700,
                                        }}>{(event.weight * 10).toFixed(1)}</div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* ── Selected Event Detail Panel ── */}
            {selectedEvent && selectedCfg && selectedSev && (
                <div style={{
                    position: 'absolute', bottom: 16, left: 16, zIndex: 25,
                    width: 320, maxWidth: 'calc(100% - 32px)',
                    background: 'rgba(2,6,23,0.94)', backdropFilter: 'blur(14px)',
                    border: `1px solid ${selectedCfg.color}44`,
                    borderRadius: '16px', overflow: 'hidden',
                    boxShadow: `0 20px 40px rgba(0,0,0,0.6), 0 0 30px ${selectedCfg.glowColor}15`,
                    animation: 'slideUp 0.3s ease',
                }}>
                    {/* Header bar */}
                    <div style={{
                        background: `linear-gradient(135deg, ${selectedCfg.color}22, transparent)`,
                        padding: '14px 16px 10px',
                        borderBottom: `1px solid ${selectedCfg.color}22`,
                        display: 'flex', alignItems: 'flex-start', gap: 10,
                    }}>
                        <span style={{ fontSize: 28 }}>{selectedCfg.icon}</span>
                        <div style={{ flex: 1 }}>
                            <div style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 800, lineHeight: 1.3 }}>
                                {selectedEvent.title || selectedCfg.label}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                                <span style={{
                                    background: selectedSev.bg, border: `1px solid ${selectedSev.color}55`,
                                    borderRadius: 6, padding: '2px 8px',
                                    color: selectedSev.color, fontSize: 10, fontWeight: 700,
                                }}>● {selectedSev.label}</span>
                                <span style={{
                                    background: selectedCfg.color + '22', border: `1px solid ${selectedCfg.color}55`,
                                    borderRadius: 6, padding: '2px 8px',
                                    color: selectedCfg.color, fontSize: 10, fontWeight: 700,
                                }}>{selectedCfg.label}</span>
                            </div>
                        </div>
                        {/* Close button */}
                        <button
                            onClick={() => { setSelectedEvent(null); setIsAutoRotating(true); }}
                            style={{
                                background: 'rgba(255,255,255,0.08)', border: 'none',
                                borderRadius: 8, width: 28, height: 28,
                                color: '#94a3b8', fontSize: 14, cursor: 'pointer',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={(e) => { (e.target as HTMLElement).style.background = 'rgba(239,68,68,0.3)'; (e.target as HTMLElement).style.color = '#ef4444'; }}
                            onMouseLeave={(e) => { (e.target as HTMLElement).style.background = 'rgba(255,255,255,0.08)'; (e.target as HTMLElement).style.color = '#94a3b8'; }}
                        >✕</button>
                    </div>
                    {/* Content grid */}
                    <div style={{ padding: '12px 16px' }}>
                        {/* Description */}
                        {selectedEvent.description && (
                            <div style={{
                                color: '#cbd5e1', fontSize: 11, lineHeight: 1.5,
                                marginBottom: 12, paddingBottom: 10,
                                borderBottom: '1px solid rgba(255,255,255,0.06)',
                            }}>{selectedEvent.description}</div>
                        )}
                        {/* Info grid */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px' }}>
                            <div>
                                <div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 2 }}>LOCALIZAÇÃO</div>
                                <div style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <span style={{ opacity: 0.7 }}>📍</span> {selectedEvent.location || 'N/A'}
                                </div>
                            </div>
                            <div>
                                <div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 2 }}>SEVERIDADE</div>
                                <div style={{ color: selectedSev.color, fontSize: 18, fontWeight: 800 }}>
                                    {(selectedEvent.weight * 10).toFixed(1)}
                                    <span style={{ fontSize: 10, color: '#64748b', fontWeight: 500 }}> / 10</span>
                                </div>
                            </div>
                            <div>
                                <div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 2 }}>DATA</div>
                                <div style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600 }}>
                                    {selectedEvent.date ? new Date(selectedEvent.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : 'N/A'}
                                </div>
                            </div>
                            <div>
                                <div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 2 }}>COORDENADAS</div>
                                <div style={{ color: '#94a3b8', fontSize: 10, fontFamily: 'monospace' }}>
                                    {selectedEvent.lat.toFixed(3)}°, {selectedEvent.lng.toFixed(3)}°
                                </div>
                            </div>
                        </div>
                        {/* Source */}
                        {selectedEvent.source && (
                            <div style={{
                                marginTop: 10, paddingTop: 8,
                                borderTop: '1px solid rgba(255,255,255,0.06)',
                                color: '#64748b', fontSize: 9, display: 'flex', alignItems: 'center', gap: 4,
                            }}>
                                <span>📡</span> Fonte: <span style={{ color: '#94a3b8', fontWeight: 600 }}>{selectedEvent.source}</span>
                            </div>
                        )}
                        {/* Severity bar */}
                        <div style={{ marginTop: 10 }}>
                            <div style={{
                                width: '100%', height: 4, borderRadius: 4,
                                background: 'rgba(255,255,255,0.06)', overflow: 'hidden',
                            }}>
                                <div style={{
                                    width: `${selectedEvent.weight * 100}%`, height: '100%',
                                    borderRadius: 4,
                                    background: `linear-gradient(90deg, ${selectedSev.color}88, ${selectedSev.color})`,
                                    transition: 'width 0.5s ease',
                                }} />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Event type legend — bottom left (only when no detail panel) */}
            {!selectedEvent && presentTypes.length > 0 && (
                <div style={{
                    position: 'absolute', bottom: 16, left: 16, zIndex: 20,
                    background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '12px', padding: '10px 14px',
                    display: 'flex', flexDirection: 'column', gap: 6,
                }}>
                    <span style={{ color: '#64748b', fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', marginBottom: 2 }}>TIPOS DE EVENTO</span>
                    {presentTypes.map(({ key, cfg }) => (
                        <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: 13 }}>{cfg.icon}</span>
                            <span style={{ color: cfg.color, fontSize: 10, fontWeight: 600 }}>{cfg.label}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Stat pill — bottom right (only when no sidebar) */}
            {!showSidebar && (
                <div style={{
                    position: 'absolute', bottom: 16, right: 16, zIndex: 20,
                    background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '12px', padding: '10px 16px',
                    display: 'flex', flexDirection: 'column', gap: 4,
                    textAlign: 'right',
                }}>
                    <span style={{ color: '#64748b', fontSize: 9, fontWeight: 700, letterSpacing: '0.1em' }}>TOP SEVERIDADE</span>
                    {[...events].sort((a, b) => b.weight - a.weight).slice(0, 3).map((e, i) => {
                        const cfg = getEventConfig(e.type);
                        return (
                            <div
                                key={i}
                                onClick={() => handleSelectEvent(e)}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: 6,
                                    cursor: 'pointer', padding: '2px 0',
                                    transition: 'opacity 0.2s',
                                }}
                                onMouseEnter={(ev) => { (ev.currentTarget as HTMLElement).style.opacity = '0.7'; }}
                                onMouseLeave={(ev) => { (ev.currentTarget as HTMLElement).style.opacity = '1'; }}
                            >
                                <span style={{ fontSize: 11 }}>{cfg.icon}</span>
                                <span style={{ color: '#e2e8f0', fontSize: 10, fontWeight: 600 }}>{(e.weight * 10).toFixed(1)}</span>
                                <span style={{ color: cfg.color, fontSize: 9 }}>{cfg.label}</span>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Globe */}
            <Globe
                ref={globeEl}
                width={dimensions.width}
                height={dimensions.height}

                // Textures
                globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
                bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
                backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"

                // Atmosphere glow
                showAtmosphere={true}
                atmosphereColor="rgba(99, 102, 241, 0.35)"
                atmosphereAltitude={0.18}

                // Rings for severity pulse
                ringsData={ringsData}
                ringColor={(d: any) => (t: number) => `${d.color}${Math.max(0, (1 - t)).toFixed(2)})`}
                ringMaxRadius="maxR"
                ringPropagationSpeed="propagationSpeed"
                ringRepeatPeriod="repeatPeriod"
                ringResolution={64}

                // Animated arcs between top-severity events
                arcsData={arcsData}
                arcColor="color"
                arcStroke="stroke"
                arcDashLength={0.4}
                arcDashGap={0.2}
                arcDashAnimateTime={2000}
                arcAltitudeAutoScale={0.3}

                // Custom HTML markers
                htmlElementsData={ringsData}
                htmlElement={buildMarker}
            />

            {/* CSS keyframe injected once */}
            <style>{`
                @keyframes pulse-dot {
                    0%,100% { opacity:1; transform:scale(1); }
                    50%      { opacity:0.6; transform:scale(1.4); }
                }
                @keyframes slideUp {
                    from { opacity:0; transform:translateY(16px); }
                    to   { opacity:1; transform:translateY(0); }
                }
                div::-webkit-scrollbar { width:4px; }
                div::-webkit-scrollbar-track { background:transparent; }
                div::-webkit-scrollbar-thumb { background:rgba(99,102,241,0.3); border-radius:4px; }
            `}</style>
        </div>
    );
}
