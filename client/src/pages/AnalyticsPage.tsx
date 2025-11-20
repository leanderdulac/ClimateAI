import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useTranslation } from '@/hooks/useTranslation';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  DollarSign,
  Calendar,
  MapPin,
  Cloud,
  Thermometer,
  Droplets,
  Wind
} from "lucide-react";

export function AnalyticsPage() {
  const { t } = useTranslation();
  return (
    <DashboardLayout
      title={t('analytics.title')}
      subtitle={t('analytics.subtitle')}
    >
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('analytics.metrics.totalVolume')}</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">R$ 2.4M</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                +12.5%
              </span>
              {t('analytics.metrics.lastMonth')}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('analytics.metrics.activeTokens')}</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">89</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                +8.2%
              </span>
              {t('analytics.metrics.newTokensMonth')}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('analytics.metrics.activeUsers')}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-red-600 flex items-center gap-1">
                <TrendingDown className="h-3 w-3" />
                -2.1%
              </span>
              {t('analytics.metrics.lastWeek')}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('analytics.metrics.climateEvents')}</CardTitle>
            <Cloud className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">156</div>
            <p className="text-xs text-muted-foreground">
              {t('analytics.metrics.monitoredToday')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>{t('analytics.performance.title')}</CardTitle>
            <CardDescription>
              {t('analytics.performance.subtitle')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-gradient-to-br from-blue-50 to-green-50 rounded-lg">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 text-blue-500 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Gráfico de Performance</p>
                <p className="text-xs text-gray-500 mt-1">Implementação em desenvolvimento</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('analytics.distribution.title')}</CardTitle>
            <CardDescription>
              {t('analytics.distribution.subtitle')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-blue-500" />
                  <span className="text-sm">Sudeste</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-200 rounded-full">
                    <div className="w-3/4 h-2 bg-blue-500 rounded-full"></div>
                  </div>
                  <span className="text-sm font-medium">75%</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Sul</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-200 rounded-full">
                    <div className="w-1/2 h-2 bg-green-500 rounded-full"></div>
                  </div>
                  <span className="text-sm font-medium">50%</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-orange-500" />
                  <span className="text-sm">Nordeste</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-200 rounded-full">
                    <div className="w-1/4 h-2 bg-orange-500 rounded-full"></div>
                  </div>
                  <span className="text-sm font-medium">25%</span>
                </div>
              </div>
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
                <p className="text-sm font-medium">Novo token criado</p>
                <p className="text-xs text-gray-600">Token de seca na região Sudeste - Valor: R$ 50.000</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">2h atrás</p>
                <Badge variant="secondary" className="text-xs">Sucesso</Badge>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 border rounded-lg">
              <div className="p-2 bg-blue-100 rounded-full">
                <Thermometer className="h-4 w-4 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Alerta climático detectado</p>
                <p className="text-xs text-gray-600">Temperatura acima do normal em São Paulo</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">4h atrás</p>
                <Badge variant="outline" className="text-xs">Alerta</Badge>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 border rounded-lg">
              <div className="p-2 bg-purple-100 rounded-full">
                <Users className="h-4 w-4 text-purple-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Novo usuário registrado</p>
                <p className="text-xs text-gray-600">Empresa agrícola do Paraná aderiu à plataforma</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">6h atrás</p>
                <Badge variant="secondary" className="text-xs">Registro</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
