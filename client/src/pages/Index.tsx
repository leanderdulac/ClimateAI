import { lazy, Suspense, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { LocationSelector } from "@/components/LocationSelector";
import { MapDisplay } from "@/components/MapDisplay";
import { WeatherWidget } from "@/components/WeatherWidget";
import { WeatherNextEnsembleWidget } from "@/components/WeatherNextEnsembleWidget";
import { BaseL2CommandCenter } from "@/components/BaseL2CommandCenter";
import { InsuranceRecommendation } from "@/components/InsuranceRecommendation";
import { AgriStrategyPanel } from "@/components/AgriStrategyPanel";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { usePeriod } from "@/lib/PeriodContext";
import { Globe, TrendingUp, DollarSign, Zap, Cloud, Shield, Sparkles, Coins } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";

const ClimateDataWidget = lazy(() =>
  import("@/components/ClimateDataWidget").then((module) => ({ default: module.ClimateDataWidget }))
);
const PricingSimulator = lazy(() =>
  import("@/components/PricingSimulator").then((module) => ({ default: module.PricingSimulator }))
);

function useDeferredSection() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current || visible) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: '300px 0px', threshold: 0.1 }
    );

    observer.observe(ref.current);

    return () => observer.disconnect();
  }, [visible]);

  return { ref, visible };
}

function DeferredSection({
  children,
  minHeightClassName,
}: {
  children: React.ReactNode;
  minHeightClassName: string;
}) {
  const { ref, visible } = useDeferredSection();

  return (
    <div ref={ref}>
      {visible ? (
        children
      ) : (
        <div className="space-y-4 rounded-3xl border border-border/60 bg-card/40 p-6">
          <Skeleton className="h-8 w-56 bg-muted" />
          <Skeleton className={`w-full rounded-xl bg-muted ${minHeightClassName}`} />
        </div>
      )}
    </div>
  );
}

function PeriodButtons() {
  const { selectedPeriod, setSelectedPeriod } = usePeriod();
  const periods = [7, 30, 90] as const;

  return (
    <div className="flex flex-wrap gap-2">
      {periods.map((days) => (
        <Button
          key={days}
          variant={selectedPeriod === days ? "default" : "outline"}
          size="sm"
          onClick={() => setSelectedPeriod(days)}
          className={
            selectedPeriod === days
              ? "rounded-full shadow-md shadow-primary/25"
              : "rounded-full border-border/80 hover:bg-muted/50"
          }
        >
          {days}D
        </Button>
      ))}
    </div>
  );
}

const STATS = [
  { icon: TrendingUp, label: 'dashboard.stats.growth', value: '+24.5%', chip: 'border-emerald-500/20', iconWrap: 'bg-emerald-500/10 text-emerald-400' },
  { icon: Globe, label: 'dashboard.stats.monitored', value: '1.2M+', chip: 'border-blue-500/20', iconWrap: 'bg-blue-500/10 text-blue-400' },
  { icon: DollarSign, label: 'dashboard.stats.value', value: '$5.2B', chip: 'border-amber-500/20', iconWrap: 'bg-amber-500/10 text-amber-400' },
  { icon: Shield, label: 'dashboard.stats.accuracy', value: '99.9%', chip: 'border-primary/20', iconWrap: 'bg-primary/10 text-primary' },
] as const;

export function IndexPage() {
  const { t } = useTranslation();

  const startInsuranceJourney = () => {
    window.dispatchEvent(new CustomEvent('climateai:insurance-intent', {
      detail: {
        active: true,
        source: 'dashboard-hero-cta',
      },
    }));

    const pricing = document.querySelector('.pricing-simulator');
    if (pricing) {
      pricing.scrollIntoView({ behavior: 'smooth' });
      return;
    }

    const dashboard = document.querySelector('#dashboard');
    dashboard?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <DashboardLayout>
      <section className="relative mb-10 overflow-hidden rounded-3xl border border-border/70 bg-card/50 backdrop-blur-xl">
        <div className="absolute inset-0 bg-gradient-mesh opacity-80" />
        <div className="relative z-10 px-5 py-10 text-center sm:px-10 md:py-14">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
            <Sparkles className="h-4 w-4" />
            {t('dashboard.badge')}
          </div>

          <h1 className="mb-5 font-display text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl">
            <span className="text-gradient-primary">ClimateWise</span>
            <span className="ml-3 inline-block animate-float">🌍</span>
          </h1>

          <p className="mx-auto mb-8 max-w-3xl text-base leading-relaxed text-muted-foreground md:text-xl">
            {t('dashboard.subtitle')}
          </p>

          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button
              size="lg"
              className="h-12 rounded-full px-8 text-base shadow-lg shadow-primary/25 hover:shadow-primary/40"
              onClick={() => {
                const dashboard = document.querySelector('#dashboard');
                if (dashboard) {
                  dashboard.scrollIntoView({ behavior: 'smooth' });
                } else {
                  const dataWidget = document.querySelector('.climate-data-widget');
                  dataWidget?.scrollIntoView({ behavior: 'smooth' });
                }
              }}
            >
              <Zap className="mr-2 h-5 w-5" />
              {t('dashboard.start')}
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="h-12 rounded-full border-border/80 px-8 text-base hover:bg-muted/50"
              onClick={() => {
                const dataWidget = document.querySelector('.climate-data-widget');
                if (dataWidget) {
                  dataWidget.scrollIntoView({ behavior: 'smooth' });
                } else {
                  const statsSection = document.querySelector('.stats-section');
                  statsSection?.scrollIntoView({ behavior: 'smooth' });
                }
              }}
            >
              <Globe className="mr-2 h-5 w-5" />
              {t('dashboard.explore')}
            </Button>
            <Button
              size="lg"
              variant="secondary"
              className="h-12 rounded-full px-8 text-base"
              onClick={startInsuranceJourney}
            >
              <Shield className="mr-2 h-5 w-5" />
              Quero cotar seguro climático
            </Button>
          </div>
        </div>
      </section>

      <section className="stats-section py-2">
        <div className="mb-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map((stat) => (
            <Card key={stat.label} className={`cc-chip border ${stat.chip} bg-card/50 p-0 shadow-none hover:border-primary/30`}>
              <CardContent className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <div className={`rounded-xl p-2.5 ${stat.iconWrap}`}>
                    <stat.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {t(stat.label)}
                    </div>
                    <div className="font-display text-2xl font-bold text-foreground">{stat.value}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mb-16" id="dashboard">
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-primary/10 p-2">
                <Cloud className="h-6 w-6 text-primary" />
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Operations
                </div>
                <h2 className="font-display text-2xl font-bold text-foreground md:text-3xl">
                  {t('dashboard.title')}
                </h2>
              </div>
            </div>
            <PeriodButtons />
          </div>

          <div className="mb-8">
            <BaseL2CommandCenter />
          </div>

          <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2 lg:items-stretch">
            <div className="h-full">
              <LocationSelector />
            </div>
            <div className="h-full">
              <WeatherWidget />
            </div>
          </div>

          <div className="mb-8">
            <WeatherNextEnsembleWidget />
          </div>

          <div className="mb-8">
            <MapDisplay />
          </div>

          <div className="mb-8">
            <InsuranceRecommendation />
          </div>

          <div className="climate-data-widget mb-8">
            <DeferredSection minHeightClassName="h-[520px]">
              <Suspense fallback={<Skeleton className="h-[520px] w-full rounded-3xl bg-muted" />}>
                <ClimateDataWidget />
              </Suspense>
            </DeferredSection>
          </div>

          <div className="mb-12">
            <DeferredSection minHeightClassName="h-[640px]">
              <Suspense fallback={<Skeleton className="h-[640px] w-full rounded-3xl bg-muted" />}>
                <PricingSimulator />
              </Suspense>
            </DeferredSection>
          </div>

          <div className="mb-12">
            <AgriStrategyPanel />
          </div>
        </div>

        <div className="relative mb-12 overflow-hidden rounded-3xl border border-border/70 bg-card/50 backdrop-blur-md" id="tokenization-section">
          <div className="absolute inset-0 bg-gradient-ocean opacity-10" />
          <div className="relative flex flex-col items-center justify-between gap-10 p-8 md:flex-row md:p-14">
            <div className="flex-1">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold text-primary">{t('dashboard.tokenization.badge')}</span>
              </div>
              <h2 className="mb-4 font-display text-3xl font-bold text-foreground md:text-4xl">
                {t('dashboard.tokenization.title')}
              </h2>
              <p className="mb-8 max-w-xl text-lg leading-relaxed text-muted-foreground">
                {t('dashboard.tokenization.desc')}
              </p>
              <Button
                onClick={() => window.location.href = '/tokenization'}
                size="lg"
                className="rounded-full px-8 shadow-lg shadow-primary/20"
              >
                <Zap className="mr-2 h-5 w-5" />
                {t('dashboard.tokenization.cta')}
              </Button>
            </div>
            <div className="relative hidden md:block">
              <div className="absolute -right-10 -top-10 h-64 w-64 animate-pulse-slow rounded-full bg-gradient-primary opacity-20 blur-3xl" />
              <div className="relative z-10 rounded-2xl border border-border/50 bg-card p-6 shadow-2xl">
                <Coins className="h-24 w-24 text-primary" />
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-border/60 bg-muted/20 py-16 text-center">
          <div className="mx-auto max-w-3xl px-4">
            <h3 className="mb-5 font-display text-3xl font-bold text-foreground md:text-4xl">
              {t('dashboard.footer.cta.title')}
            </h3>
            <p className="mb-8 text-lg font-light text-muted-foreground md:text-xl">
              {t('dashboard.footer.cta.desc')}
            </p>
            <div className="flex flex-col justify-center gap-3 sm:flex-row">
              <Button
                size="lg"
                className="h-12 rounded-full px-10 text-lg shadow-xl"
              >
                <Sparkles className="mr-2 h-5 w-5" />
                {t('dashboard.footer.cta.primary')}
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="h-12 rounded-full border-border/80 px-10 text-lg hover:bg-muted/50"
              >
                <Globe className="mr-2 h-5 w-5" />
                {t('dashboard.footer.cta.secondary')}
              </Button>
            </div>
          </div>
        </div>
      </section>
    </DashboardLayout>
  );
}
