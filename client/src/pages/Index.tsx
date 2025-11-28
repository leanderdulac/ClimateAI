import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { LocationSelector } from "@/components/LocationSelector";
import { MapDisplay } from "@/components/MapDisplay";
import { WeatherWidget } from "@/components/WeatherWidget";
import { ClimateDataWidget } from "@/components/ClimateDataWidget";
import { PricingSimulator } from "@/components/PricingSimulator";
import { DashboardLayout } from "@/components/DashboardLayout";
import { LocationProvider } from "@/lib/LocationContext";
import { PeriodProvider, usePeriod } from "@/lib/PeriodContext";
import { Globe, TrendingUp, DollarSign, Zap, Cloud, Shield, Sparkles } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";

function PeriodButtons() {
  const { selectedPeriod, setSelectedPeriod } = usePeriod();

  return (
    <div className="ml-auto flex gap-2">
      <Button
        variant={selectedPeriod === 7 ? "default" : "outline"}
        size="sm"
        onClick={() => setSelectedPeriod(7)}
        className="transition-all hover:scale-105"
      >
        7D
      </Button>
      <Button
        variant={selectedPeriod === 30 ? "default" : "outline"}
        size="sm"
        onClick={() => setSelectedPeriod(30)}
        className="transition-all hover:scale-105"
      >
        30D
      </Button>
      <Button
        variant={selectedPeriod === 90 ? "default" : "outline"}
        size="sm"
        onClick={() => setSelectedPeriod(90)}
        className="transition-all hover:scale-105"
      >
        90D
      </Button>
    </div>
  );
}

export function IndexPage() {
  const { t } = useTranslation();

  return (
    <DashboardLayout>
      <LocationProvider>
        <PeriodProvider>
          {/* Hero Section with Animated Gradient */}
          <section className="relative py-20 md:py-32 overflow-hidden">
            {/* Animated gradient background */}
            <div className="absolute inset-0 animated-gradient opacity-10"></div>

            {/* Floating orbs for visual interest */}
            <div className="absolute top-20 left-10 w-72 h-72 bg-cyan-400/20 rounded-full blur-3xl animate-pulse"></div>
            <div className="absolute bottom-20 right-10 w-96 h-96 bg-emerald-400/20 rounded-full blur-3xl animate-pulse animation-delay-500"></div>

            <div className="container mx-auto max-w-7xl px-4 relative z-10">
              <div className="text-center mb-16">
                {/* Badge with glow effect */}
                <div className="inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500/10 to-emerald-500/10 border border-cyan-500/20 px-6 py-3 rounded-full text-sm font-medium text-cyan-700 mb-8 backdrop-blur-sm hover:scale-105 transition-transform">
                  <Sparkles className="h-4 w-4 text-cyan-600" />
                  {t('dashboard.badge')}
                </div>

                {/* Main title with gradient */}
                <h1 className="text-6xl md:text-8xl font-black mb-6 leading-tight">
                  <span className="gradient-text">ClimateWise</span>
                  <span className="inline-block ml-3 text-6xl md:text-7xl float">🌍</span>
                </h1>

                {/* Subtitle with better typography */}
                <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-12 leading-relaxed font-light">
                  {t('dashboard.subtitle')}
                </p>

                {/* CTA buttons with premium styling */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button
                    size="lg"
                    className="btn-premium text-lg px-8 py-6 shadow-2xl"
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
                    className="text-lg px-8 py-6 border-2 hover:bg-gradient-to-r hover:from-cyan-50 hover:to-emerald-50 transition-all hover:scale-105 hover:border-cyan-500"
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
                </div>
              </div>
            </div>
          </section>

          {/* Stats Section with Glassmorphism */}
          <section className="py-16 stats-section relative">
            <div className="container mx-auto max-w-7xl px-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-20">
                <Card className="glass-card hover-lift border-0 shadow-xl overflow-hidden group">
                  <CardContent className="p-8 text-center relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <TrendingUp className="h-10 w-10 text-blue-600 mx-auto mb-4 group-hover:scale-110 transition-transform" />
                    <div className="text-4xl font-black bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent mb-2">+24.5%</div>
                    <div className="text-sm font-medium text-blue-700">{t('dashboard.stats.growth')}</div>
                  </CardContent>
                </Card>

                <Card className="glass-card hover-lift border-0 shadow-xl overflow-hidden group">
                  <CardContent className="p-8 text-center relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <Globe className="h-10 w-10 text-emerald-600 mx-auto mb-4 group-hover:scale-110 transition-transform" />
                    <div className="text-4xl font-black bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent mb-2">1.2M+</div>
                    <div className="text-sm font-medium text-emerald-700">{t('dashboard.stats.monitored')}</div>
                  </CardContent>
                </Card>

                <Card className="glass-card hover-lift border-0 shadow-xl overflow-hidden group">
                  <CardContent className="p-8 text-center relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <DollarSign className="h-10 w-10 text-purple-600 mx-auto mb-4 group-hover:scale-110 transition-transform" />
                    <div className="text-4xl font-black bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">$5.2B</div>
                    <div className="text-sm font-medium text-purple-700">{t('dashboard.stats.value')}</div>
                  </CardContent>
                </Card>

                <Card className="glass-card hover-lift border-0 shadow-xl overflow-hidden group">
                  <CardContent className="p-8 text-center relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <Shield className="h-10 w-10 text-orange-600 mx-auto mb-4 group-hover:scale-110 transition-transform" />
                    <div className="text-4xl font-black bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent mb-2">99.9%</div>
                    <div className="text-sm font-medium text-orange-700">{t('dashboard.stats.accuracy')}</div>
                  </CardContent>
                </Card>
              </div>

              {/* Main Dashboard Section */}
              <div className="mb-16">
                <div className="flex items-center gap-3 mb-10">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 shadow-lg glow">
                    <Cloud className="h-7 w-7 text-white" />
                  </div>
                  <h2 className="text-4xl font-black bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
                    Climate Dashboard
                  </h2>
                  <PeriodButtons />
                </div>

                {/* Top Section - Location and Weather */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
                  <div className="hover-lift">
                    <LocationSelector />
                  </div>
                  <div className="hover-lift">
                    <WeatherWidget />
                  </div>
                </div>

                {/* Interactive Map Section */}
                <div className="mb-12 hover-lift">
                  <MapDisplay />
                </div>

                {/* Climate Data Analysis */}
                <div className="mb-12 hover-lift">
                  <ClimateDataWidget />
                </div>

                {/* Pricing Simulator - Full Width with More Space */}
                <div className="mb-16 hover-lift">
                  <PricingSimulator />
                </div>
              </div>

              {/* Tokenization Section with Modern Design */}
              <div className="mb-12" id="tokenization-section">
                <Card className="glass-card border-0 shadow-2xl overflow-hidden hover-lift">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-blue-500/5 to-cyan-500/5"></div>
                  <CardContent className="p-10 relative">
                    <div className="flex items-center justify-between flex-wrap gap-6">
                      <div className="flex-1 min-w-[300px]">
                        <div className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-500/10 to-blue-500/10 px-4 py-2 rounded-full mb-4">
                          <Sparkles className="h-4 w-4 text-purple-600" />
                          <span className="text-sm font-semibold text-purple-700">Blockchain Powered</span>
                        </div>
                        <h2 className="text-3xl font-black mb-4 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                          Tokenização & Smart Contracts
                        </h2>
                        <p className="text-muted-foreground mb-6 text-lg leading-relaxed">
                          Sistema avançado de tokenização de eventos climáticos e execução de contratos inteligentes
                        </p>
                        <Button
                          onClick={() => window.location.href = '/tokenization'}
                          className="btn-premium bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                          size="lg"
                        >
                          <Zap className="mr-2 h-5 w-5" />
                          Acessar Tokenização e Contratos
                        </Button>
                      </div>
                      <div className="hidden md:block">
                        <div className="relative">
                          <div className="w-32 h-32 bg-gradient-to-br from-purple-400 to-blue-400 rounded-3xl rotate-12 opacity-20 blur-xl"></div>
                          <Zap className="h-24 w-24 text-purple-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 float" />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* CTA Section with Premium Design */}
              <div className="text-center py-16">
                <Card className="border-0 shadow-2xl overflow-hidden relative group">
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 opacity-90 group-hover:opacity-100 transition-opacity"></div>
                  <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjEiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-30"></div>
                  <CardContent className="p-16 relative z-10">
                    <div className="max-w-3xl mx-auto">
                      <h3 className="text-5xl font-black text-white mb-6 leading-tight">
                        Ready to Transform Climate Risk?
                      </h3>
                      <p className="text-xl text-white/90 mb-10 leading-relaxed font-light">
                        Join thousands of users leveraging ClimateWise for advanced climate analytics and risk management
                      </p>
                      <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Button
                          size="lg"
                          className="bg-white text-cyan-700 hover:bg-white/90 font-bold text-lg px-10 py-6 shadow-2xl hover:scale-105 transition-all"
                        >
                          <Sparkles className="mr-2 h-5 w-5" />
                          Get Started
                        </Button>
                        <Button
                          size="lg"
                          variant="outline"
                          className="bg-transparent border-2 border-white text-white hover:bg-white/10 font-bold text-lg px-10 py-6 hover:scale-105 transition-all"
                        >
                          <Globe className="mr-2 h-5 w-5" />
                          Schedule Demo
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </section>
        </PeriodProvider>
      </LocationProvider>
    </DashboardLayout>
  );
}
