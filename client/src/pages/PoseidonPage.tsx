import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import { Icon } from 'leaflet';
import {
  Activity,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  MapPin,
  Radio,
  Waves,
} from 'lucide-react';

import markerIconPng from 'leaflet/dist/images/marker-icon.png';
import markerIcon2xPng from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadowPng from 'leaflet/dist/images/marker-shadow.png';

import { DashboardLayout } from '@/components/DashboardLayout';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import {
  chatPoseidon,
  getCcoCma,
  getCcoConnectors,
  getCcoDemanda,
  getCcoIncidents,
  getCcoPsa,
  getCcoSystems,
  getPoseidonStatus,
  postCcoDemoGeosmina,
  postCcoDemoGuandu50,
  type CcoCma,
  type CcoConnector,
  type CcoDemanda,
  type CcoIncident,
  type CcoPsa,
  type CcoSystemsData,
  type PoseidonStatus,
} from '@/lib/api/poseidon';
import { useTranslation } from '@/hooks/useTranslation';

const defaultIcon = new Icon({
  iconUrl: markerIconPng,
  iconRetinaUrl: markerIcon2xPng,
  shadowUrl: markerShadowPng,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

type Turn = { role: 'user' | 'assistant'; content: string; tools?: string[] };

function levelClass(level?: string) {
  if (level === 'critico') return 'bg-red-600 text-white';
  if (level === 'alerta') return 'bg-amber-500 text-slate-950';
  if (level === 'advisory') return 'bg-sky-600 text-white';
  return 'bg-emerald-600 text-white';
}

function fmtLs(value?: number) {
  if (value == null || Number.isNaN(value)) return '—';
  return `${Math.round(value).toLocaleString('pt-BR')} L/s`;
}

function CcoMap({
  systems,
  cma,
}: {
  systems: CcoSystemsData | null;
  cma: CcoCma | null;
}) {
  const markers = useMemo(() => {
    const items: Array<{ id: string; name: string; lat: number; lon: number; detail: string }> = [];
    for (const system of systems?.systems ?? []) {
      items.push({
        id: system.id,
        name: system.name,
        lat: system.lat,
        lon: system.lon,
        detail: `${system.kind} · ${fmtLs(system.production_l_s)} / ${fmtLs(system.capacity_l_s)}`,
      });
    }
    for (const point of systems?.delivery_points ?? []) {
      items.push({
        id: point.id,
        name: point.name,
        lat: point.lat,
        lon: point.lon,
        detail: point.kind,
      });
    }
    if (cma) {
      items.push({
        id: cma.id,
        name: cma.name,
        lat: cma.lat,
        lon: cma.lon,
        detail: `CMA · ${cma.cameras} câmeras / ${cma.points} pontos (fixture)`,
      });
    }
    return items;
  }, [systems, cma]);

  return (
    <div className="h-[22rem] overflow-hidden rounded-lg border border-cyan-900/60">
      <MapContainer
        center={[-22.82, -43.35]}
        zoom={9}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={false}
        className="z-10 h-full w-full bg-slate-900"
      >
        <TileLayer
          attribution='&copy; OpenStreetMap &copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {markers.map((marker) => (
          <Marker key={marker.id} position={[marker.lat, marker.lon]} icon={defaultIcon}>
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{marker.name}</p>
                <p>{marker.detail}</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

function BriefingDrawer({
  open,
  onToggle,
  t,
}: {
  open: boolean;
  onToggle: () => void;
  t: (key: string) => string;
}) {
  const [status, setStatus] = useState<PoseidonStatus | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    getPoseidonStatus()
      .then(setStatus)
      .catch((exc: Error) => setError(exc.message));
  }, [open]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, busy]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    const next: Turn[] = [...turns, { role: 'user', content: text }];
    setTurns(next);
    setDraft('');
    setBusy(true);
    setError(null);
    try {
      const result = await chatPoseidon(next.map(({ role, content }) => ({ role, content })));
      setTurns([
        ...next,
        {
          role: 'assistant',
          content: result.reply || t('poseidon.emptyReply'),
          tools: result.tool_trace.map((item) => `${item.tool}:${item.status ?? '?'}`),
        },
      ]);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t('poseidon.error'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="border-cyan-900/50 bg-slate-900/80 text-slate-100">
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 py-3">
        <Waves className="h-5 w-5 text-cyan-400" />
        <div className="flex-1">
          <CardTitle className="text-base text-slate-100">{t('poseidon.briefing')}</CardTitle>
          <CardDescription className="text-slate-400">
            {status?.ollama && status.model_present ? t('poseidon.online') : t('poseidon.offline')}
          </CardDescription>
        </div>
        <Badge variant={status?.model_present ? 'default' : 'secondary'}>
          {status?.model ?? 'poseidon'}
        </Badge>
        <Button variant="ghost" size="sm" onClick={onToggle} className="text-slate-200">
          {open ? t('poseidon.briefingClose') : t('poseidon.briefingOpen')}
          {open ? <ChevronDown className="ml-1 h-4 w-4" /> : <ChevronUp className="ml-1 h-4 w-4" />}
        </Button>
      </CardHeader>
      {open && (
        <CardContent className="space-y-3">
          <p className="text-xs text-slate-400">{t('poseidon.rule')}</p>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div className="flex h-56 flex-col gap-2 overflow-y-auto rounded-md border border-slate-800 p-3">
            {turns.length === 0 && <p className="text-sm text-slate-400">{t('poseidon.hint')}</p>}
            {turns.map((turn, index) => (
              <div
                key={`${turn.role}-${index}`}
                className={`rounded-md px-3 py-2 text-sm ${
                  turn.role === 'user' ? 'ml-8 bg-cyan-950' : 'mr-8 bg-slate-800'
                }`}
              >
                <p className="whitespace-pre-wrap">{turn.content}</p>
                {turn.tools && turn.tools.length > 0 && (
                  <p className="mt-2 text-xs text-slate-400">{turn.tools.join(' · ')}</p>
                )}
              </div>
            ))}
            {busy && <p className="text-sm text-slate-400">{t('poseidon.thinking')}</p>}
            <div ref={bottom} />
          </div>
          <form onSubmit={onSubmit} className="flex gap-2">
            <Input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={t('poseidon.placeholder')}
              disabled={busy}
              className="border-slate-700 bg-slate-950 text-slate-100"
            />
            <Button type="submit" disabled={busy || !draft.trim()}>
              {t('poseidon.send')}
            </Button>
          </form>
        </CardContent>
      )}
    </Card>
  );
}

export function PoseidonPage() {
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [systems, setSystems] = useState<CcoSystemsData | null>(null);
  const [cma, setCma] = useState<CcoCma | null>(null);
  const [psa, setPsa] = useState<CcoPsa | null>(null);
  const [incidents, setIncidents] = useState<CcoIncident[]>([]);
  const [connectors, setConnectors] = useState<CcoConnector[]>([]);
  const [demanda, setDemanda] = useState<CcoDemanda | null>(null);
  const [playbook, setPlaybook] = useState<string[]>([]);
  const [briefingOpen, setBriefingOpen] = useState(false);

  const loadBoard = useCallback(async () => {
    const [sys, cmaEnv, psaEnv, incEnv, connEnv] = await Promise.all([
      getCcoSystems(),
      getCcoCma(),
      getCcoPsa(),
      getCcoIncidents(),
      getCcoConnectors(),
    ]);
    setSystems(sys.data);
    setCma(cmaEnv.data);
    setPsa(psaEnv.data);
    setIncidents(incEnv.data.incidents ?? []);
    setConnectors(connEnv.data.connectors ?? []);
    const latest = incEnv.data.incidents?.[0];
    if (latest?.playbook?.length) setPlaybook(latest.playbook);
  }, []);

  useEffect(() => {
    loadBoard().catch((exc: Error) => setError(exc.message));
  }, [loadBoard]);

  async function runAction(kind: 'geosmina' | 'guandu' | 'demanda') {
    setBusy(true);
    setError(null);
    try {
      if (kind === 'geosmina') {
        const result = await postCcoDemoGeosmina();
        setPlaybook(result.data.evaluation.sop ?? result.data.incident.playbook ?? []);
      } else if (kind === 'guandu') {
        const result = await postCcoDemoGuandu50();
        setPlaybook(result.data.incident.playbook ?? []);
      } else {
        const result = await getCcoDemanda(24);
        setDemanda(result.data);
        setPlaybook([
          result.data.note || t('poseidon.demandaNote'),
          t('poseidon.advisory'),
        ]);
      }
      await loadBoard();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t('poseidon.error'));
    } finally {
      setBusy(false);
    }
  }

  const guandu = systems?.systems.find((item) => item.id === 'guandu');
  const laranjal = systems?.systems.find((item) => item.id === 'imunana_laranjal');
  const psaLevel = psa?.psa.level ?? 'normal';
  const demandaGuandu = demanda?.series.map((row) => row.systems.guandu?.point_l_s ?? 0) ?? [];
  const demandaMax = Math.max(1, ...demandaGuandu);

  return (
    <DashboardLayout title="poseidon.title" subtitle="poseidon.subtitle">
      <div className="-mx-1 rounded-xl border border-cyan-900/40 bg-slate-950 p-4 text-slate-100 shadow-2xl">
        <div className="mb-4 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          {t('poseidon.banner')}
        </div>

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="mb-4 flex flex-wrap gap-2">
          <Button disabled={busy} onClick={() => runAction('geosmina')}>
            {t('poseidon.simulateGeosmina')}
          </Button>
          <Button disabled={busy} variant="secondary" onClick={() => runAction('guandu')}>
            {t('poseidon.simulateGuandu50')}
          </Button>
          <Button disabled={busy} variant="outline" onClick={() => runAction('demanda')}>
            {t('poseidon.forecast24h')}
          </Button>
        </div>

        <div className="grid gap-4 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-8">
            <Card className="border-cyan-900/50 bg-slate-900/70 text-slate-100">
              <CardHeader className="py-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <MapPin className="h-4 w-4 text-cyan-400" />
                  {t('poseidon.map')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CcoMap systems={systems} cma={cma} />
              </CardContent>
            </Card>

            <div className="grid gap-4 md:grid-cols-2">
              <Card className="border-cyan-900/50 bg-slate-900/70 text-slate-100">
                <CardHeader className="py-3">
                  <CardTitle className="text-base">{t('poseidon.incidents')}</CardTitle>
                </CardHeader>
                <CardContent className="max-h-64 space-y-3 overflow-y-auto text-sm">
                  {incidents.length === 0 && (
                    <p className="text-slate-400">{t('poseidon.noIncidents')}</p>
                  )}
                  {incidents.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="block w-full rounded-md border border-slate-800 p-2 text-left hover:border-cyan-700"
                      onClick={() => setPlaybook(item.playbook ?? [])}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`rounded px-1.5 py-0.5 text-[10px] uppercase ${levelClass(item.level)}`}>
                          {item.level}
                        </span>
                        <span className="font-medium">{item.title}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-400">{item.summary}</p>
                    </button>
                  ))}
                </CardContent>
              </Card>

              <Card className="border-cyan-900/50 bg-slate-900/70 text-slate-100">
                <CardHeader className="py-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                    {t('poseidon.playbook')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {playbook.length === 0 ? (
                    <p className="text-sm text-slate-400">{t('poseidon.playbookEmpty')}</p>
                  ) : (
                    <ol className="list-decimal space-y-2 pl-4 text-sm text-slate-200">
                      {playbook.map((step, index) => (
                        <li key={`${index}-${step.slice(0, 12)}`}>{step}</li>
                      ))}
                    </ol>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          <div className="space-y-4 lg:col-span-4">
            <Card className="border-cyan-900/50 bg-slate-900/70 text-slate-100">
              <CardHeader className="py-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="h-4 w-4 text-cyan-400" />
                  {t('poseidon.psa')}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${levelClass(psaLevel)}`}>
                    {psaLevel}
                  </span>
                  {Object.entries(psa?.psa.components ?? {}).map(([key, value]) => (
                    <span
                      key={key}
                      className={`rounded-full px-3 py-1 text-xs uppercase ${levelClass(value)}`}
                    >
                      {key}: {value}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-slate-400">{t('poseidon.advisory')}</p>
              </CardContent>
            </Card>

            <Card className="border-cyan-900/50 bg-slate-900/70 text-slate-100">
              <CardHeader className="py-3">
                <CardTitle className="text-base">{t('poseidon.production')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                {[guandu, laranjal].map((system) =>
                  system ? (
                    <div key={system.id}>
                      <div className="mb-1 flex justify-between">
                        <span>{system.name}</span>
                        <span>
                          {fmtLs(system.production_l_s)} / {fmtLs(system.capacity_l_s)}
                        </span>
                      </div>
                      <Progress
                        value={Math.min(100, (100 * system.production_l_s) / system.capacity_l_s)}
                        className="h-2 bg-slate-800"
                      />
                    </div>
                  ) : null
                )}
                {cma && (
                  <p className="text-xs text-slate-400">
                    {cma.name} · {cma.opened} · {cma.cameras} câmeras / {cma.points} pontos · fixture
                  </p>
                )}
              </CardContent>
            </Card>

            {demanda && (
              <Card className="border-cyan-900/50 bg-slate-900/70 text-slate-100">
                <CardHeader className="py-3">
                  <CardTitle className="text-base">{t('poseidon.forecast24h')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex h-16 items-end gap-0.5">
                    {demandaGuandu.map((value, index) => (
                      <div
                        key={index}
                        className="flex-1 rounded-t bg-cyan-500/80"
                        style={{ height: `${Math.max(8, (100 * value) / demandaMax)}%` }}
                        title={`${index}h · ${fmtLs(value)}`}
                      />
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-slate-400">{demanda.note}</p>
                </CardContent>
              </Card>
            )}

            <Card className="border-cyan-900/50 bg-slate-900/70 text-slate-100">
              <CardHeader className="py-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Radio className="h-4 w-4 text-cyan-400" />
                  {t('poseidon.connectors')}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-xs">
                {connectors.map((item) => (
                  <div key={item.id} className="flex items-center justify-between gap-2">
                    <span>{item.name}</span>
                    <span className="uppercase text-slate-400">{item.status}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="mt-4">
          <BriefingDrawer
            open={briefingOpen}
            onToggle={() => setBriefingOpen((value) => !value)}
            t={t}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}

export default PoseidonPage;
