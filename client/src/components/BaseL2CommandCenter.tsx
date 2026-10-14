import { useEffect, useState } from 'react';
import { Cpu } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { computeApi, computeStatusLabel, type ComputeStatus } from '@/lib/api/compute';
import { useTranslation } from '@/hooks/useTranslation';

const POLL_MS = 60_000;

function statusBadgeClass(status: ComputeStatus['status'] | undefined): string {
  if (status === 'online') {
    return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30';
  }
  if (status === 'offline') {
    return 'bg-amber-500/10 text-amber-600 border-amber-500/30';
  }
  return 'bg-muted text-muted-foreground border-border';
}

export function BaseL2CommandCenter() {
  const { t } = useTranslation();
  const [status, setStatus] = useState<ComputeStatus | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const next = await computeApi.getStatus();
        if (!cancelled) setStatus(next);
      } catch {
        if (!cancelled) {
          setStatus({
            status: 'offline',
            mode: 'local_fallback',
            latency_ms: null,
            last_checked: new Date().toISOString(),
          });
        }
      }
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

  return (
    <div className="w-full" data-testid="akash-depin-card">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="flex flex-col gap-3 p-4 rounded-2xl bg-gradient-to-br from-card/80 to-card/40 border border-primary/20 backdrop-blur-md shadow-sm">
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
            className={`self-start text-xs font-mono ${statusBadgeClass(status?.status)}`}
          >
            {label}
          </Badge>
        </div>
      </div>
    </div>
  );
}
