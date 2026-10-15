import { useEffect, useState } from 'react';
import { Cpu, FileCheck, Layers, Radio } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { computeApi, computeStatusLabel, type ComputeStatus } from '@/lib/api/compute';
import {
  badgeTone,
  baseBadgeLabel,
  baseBlockLabel,
  contractBadgeLabel,
  fetchBaseL2Status,
  fetchOracleCommandStatus,
  oracleBadgeLabel,
  oracleConsensusLabel,
  policyExplorerUrl,
  shortenAddress,
  type AuthStatusResult,
  type BaseL2Status,
  type OracleCommandStatus,
} from '@/lib/api/baseL2Status';
import { useTranslation } from '@/hooks/useTranslation';

const POLL_MS = 60_000;

function statusBadgeClass(tone: 'online' | 'offline' | 'expired' | 'muted'): string {
  if (tone === 'online') {
    return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30';
  }
  if (tone === 'offline' || tone === 'expired') {
    return 'bg-amber-500/10 text-amber-600 border-amber-500/30';
  }
  return 'bg-muted text-muted-foreground border-border';
}

export function BaseL2CommandCenter() {
  const { t } = useTranslation();
  const [status, setStatus] = useState<ComputeStatus | null>(null);
  const [base, setBase] = useState<AuthStatusResult<BaseL2Status> | null>(null);
  const [oracle, setOracle] = useState<AuthStatusResult<OracleCommandStatus> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const [computeSettled, baseSettled, oracleSettled] = await Promise.allSettled([
        computeApi.getStatus(),
        fetchBaseL2Status(),
        fetchOracleCommandStatus(),
      ]);
      if (cancelled) {
        return;
      }
      if (computeSettled.status === 'fulfilled') {
        setStatus(computeSettled.value);
      } else {
        setStatus({
          status: 'offline',
          mode: 'local_fallback',
          latency_ms: null,
          last_checked: new Date().toISOString(),
        });
      }
      setBase(
        baseSettled.status === 'fulfilled'
          ? baseSettled.value
          : { ok: false, reason: 'unavailable' }
      );
      setOracle(
        oracleSettled.status === 'fulfilled'
          ? oracleSettled.value
          : { ok: false, reason: 'unavailable' }
      );
    };

    void load();
    const interval = window.setInterval(() => {
      void load();
    }, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const label = computeStatusLabel(status, t);
  const policy = base?.ok ? base.data.contracts?.policy : null;
  const explorer = base?.ok ? base.data.explorer_url : null;

  return (
    <div className="w-full space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="flex flex-col gap-3 p-4 rounded-2xl bg-gradient-to-br from-card/80 to-card/40 border border-primary/20 backdrop-blur-md shadow-sm" data-testid="akash-depin-card">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary shrink-0">
              <Cpu className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {t('compute.akash.title')}
              </div>
              <div className="text-sm font-bold text-foreground">{t('compute.akash.subtitle')}</div>
            </div>
          </div>
          <Badge
            variant="outline"
            className={`self-start text-xs font-mono ${statusBadgeClass(
              status?.status === 'online'
                ? 'online'
                : status?.status === 'offline'
                  ? 'offline'
                  : 'muted'
            )}`}
          >
            {label}
          </Badge>
        </div>

        <div className="flex flex-col gap-3 p-4 rounded-2xl bg-gradient-to-br from-card/80 to-card/40 border border-blue-500/20 backdrop-blur-md shadow-sm" data-testid="base-l2-card">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-500 shrink-0">
              <Layers className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {t('compute.base.title')}
              </div>
              <div className="text-sm font-bold text-foreground font-mono">
                {baseBlockLabel(base, t)}
              </div>
            </div>
          </div>
          <Badge
            variant="outline"
            className={`self-start text-xs font-mono ${statusBadgeClass(badgeTone(base))}`}
          >
            {baseBadgeLabel(base, t)}
          </Badge>
        </div>

        <div className="flex flex-col gap-3 p-4 rounded-2xl bg-gradient-to-br from-card/80 to-card/40 border border-purple-500/20 backdrop-blur-md shadow-sm" data-testid="oracle-card">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 shrink-0">
              <Radio className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {t('compute.oracle.title')}
              </div>
              <div className="text-sm font-bold text-foreground">
                {oracleConsensusLabel(oracle, t)}
              </div>
            </div>
          </div>
          <Badge
            variant="outline"
            className={`self-start text-xs ${statusBadgeClass(badgeTone(oracle))}`}
          >
            {oracleBadgeLabel(oracle, t)}
          </Badge>
        </div>

        <div className="flex flex-col gap-3 p-4 rounded-2xl bg-gradient-to-br from-card/80 to-card/40 border border-amber-500/20 backdrop-blur-md shadow-sm" data-testid="contract-card">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-500 shrink-0">
              <FileCheck className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {t('compute.contract.title')}
              </div>
              <div className="text-xs font-mono text-muted-foreground">
                {policy ? (
                  <a
                    href={policyExplorerUrl(explorer, policy)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-foreground hover:underline"
                  >
                    {shortenAddress(policy)}
                  </a>
                ) : (
                  '—'
                )}
              </div>
            </div>
          </div>
          <Badge
            variant="outline"
            className={`self-start text-xs ${statusBadgeClass(badgeTone(base))}`}
          >
            {contractBadgeLabel(base, t)}
          </Badge>
        </div>
      </div>
    </div>
  );
}
