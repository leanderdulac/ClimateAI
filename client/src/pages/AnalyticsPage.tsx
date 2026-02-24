import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useTranslation } from '@/hooks/useTranslation';
import {
  TrendingUp,
  Activity,
  Shield,
  ArrowUpRight,
  ArrowDownRight,
  Percent
} from "lucide-react";
import { useEffect, useState } from "react";
import { parametricApi, SIPSPerformanceSummary } from "@/lib/parametricApi";
import { BrasilRiskMap } from "@/components/BrasilRiskMap";
import { RealTimeRiskMonitor } from "@/components/RealTimeRiskMonitor";
import { Skeleton } from "@/components/ui/skeleton";

export function AnalyticsPage() {
  const { t } = useTranslation();
  const [data, setData] = useState<SIPSPerformanceSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    parametricApi.getPerformanceSummary()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <DashboardLayout title={t('analytics.title')} subtitle={t('analytics.subtitle')}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
        <Skeleton className="h-[400px] w-full" />
      </DashboardLayout>
    );
  }

  const metrics = data?.dashboard_summary.current_metrics;
  const improvements = data?.dashboard_summary.improvements;

  const formatPercent = (val: number) => {
    return (val * 100).toFixed(1) + '%';
  };

  return (
    <DashboardLayout
      title={t('analytics.title')}
      subtitle={t('analytics.subtitle')}
    >
      {/* Key Metrics - SIPS PERFORMANCE */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="border-emerald-100 bg-emerald-50/10">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Margem Líquida</CardTitle>
            <TrendingUp className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-700">{formatPercent(metrics?.margem_liquida || 0)}</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
              <span className="text-emerald-600 flex items-center">
                <ArrowUpRight className="h-3 w-3" />
                {improvements?.margin_improvement}
              </span>
              vs baseline
            </p>
          </CardContent>
        </Card>

        <Card className="border-blue-100 bg-blue-50/10">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Capital Econômico</CardTitle>
            <Shield className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-700">R$ 52M</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
              <span className="text-blue-600 flex items-center">
                <ArrowUpRight className="h-3 w-3" />
                +15%
              </span>
              crescimento anual
            </p>
          </CardContent>
        </Card>

        <Card className="border-orange-100 bg-orange-50/10">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Taxa de Sinistralidade</CardTitle>
            <Activity className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-700">{formatPercent(metrics?.taxa_sinistralidade || 0)}</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
              <span className="text-emerald-600 flex items-center">
                <ArrowDownRight className="h-3 w-3" />
                {improvements?.claim_rate_improvement}
              </span>
              melhoria de eficiência
            </p>
          </CardContent>
        </Card>

        <Card className="border-purple-100 bg-purple-50/10">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SIPS Impact Score</CardTitle>
            <Percent className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-700">{data?.dashboard_summary.sips_impact_score.toFixed(1)}/100</div>
            <p className="text-xs text-muted-foreground mt-1">
              Índice de impacto atuarial otimizado
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Real-time Risk Monitor */}
      <div className="mb-8">
        <RealTimeRiskMonitor />
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          <BrasilRiskMap />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Insights Chave</CardTitle>
            <CardDescription>
              Análise automatizada do portfólio
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data?.key_findings.map((finding, i) => (
                <div key={i} className="flex gap-3 text-sm p-3 rounded-lg bg-muted/30 border border-border/50">
                  <div className="h-2 w-2 rounded-full bg-primary mt-1.5 shrink-0" />
                  <p className="text-muted-foreground">{finding}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>{t('analytics.recentActivity.title')}</CardTitle>
          <CardDescription>
            {t('analytics.recentActivity.subtitle')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 border rounded-lg">
              <div className="p-2 bg-green-100 rounded-full">
                <TrendingUp className="h-4 w-4 text-green-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Otimização de Portfólio Concluída</p>
                <p className="text-xs text-gray-600">Redução de exposição em áreas de alto risco no Nordeste.</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">2h atrás</p>
                <Badge variant="secondary" className="text-xs">Eficiência</Badge>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 border rounded-lg">
              <div className="p-2 bg-blue-100 rounded-full">
                <Shield className="h-4 w-4 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Rebalanceamento de Capital</p>
                <p className="text-xs text-gray-600">Alocação de R$ 2.5M para cobertura de Seca.</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">5h atrás</p>
                <Badge variant="outline" className="text-xs">Ajuste</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
