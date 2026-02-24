import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { LocationSelector } from "@/components/LocationSelector";
import { MapDisplay } from "@/components/MapDisplay";
import { WeatherWidget } from "@/components/WeatherWidget";
import { ClimateDataWidget } from "@/components/ClimateDataWidget";
import { InsuranceRecommendation } from "@/components/InsuranceRecommendation";
import { PricingSimulator } from "@/components/PricingSimulator";
import { DashboardLayout } from "@/components/DashboardLayout";
import { usePeriod } from "@/lib/PeriodContext";
import { Globe, TrendingUp, DollarSign, Zap, Cloud, Shield, Sparkles, Coins } from "lucide-react";
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
      {/* Hero Section with Professional Mesh Gradient */}
      <section className="relative py-20 md:py-32 overflow-hidden rounded-3xl mb-12 bg-gradient-mesh">
        <div className="absolute inset-0 bg-background/5 backdrop-blur-3xl"></div>

        <div className="container mx-auto max-w-7xl px-4 relative z-10 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/20 px-4 py-2 rounded-full text-sm font-medium text-primary mb-8 animate-fade-in">
            <Sparkles className="h-4 w-4" />
            {t('dashboard.badge')}
          </div>

          {/* Main title */}
          <h1 className="text-5xl md:text-7xl font-display font-bold mb-6 tracking-tight text-foreground animate-slide-up">
            <span className="bg-gradient-primary bg-clip-text text-transparent">ClimateWise</span>
            <span className="inline-block ml-3 animate-float">🌍</span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-10 leading-relaxed animate-slide-up animation-delay-200">
            {t('dashboard.subtitle')}
          </p>

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up animation-delay-300">
            <Button
              size="lg"
              className="rounded-full text-lg px-8 h-14 shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all hover:scale-105"
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
              className="rounded-full text-lg px-8 h-14 border-2 hover:bg-muted/50 transition-all hover:scale-105"
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
      </section>

      {/* Stats Section with Glassmorphism Cards */}
      <section className="py-8 stats-section">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-20">
          {[
            { icon: TrendingUp, label: 'dashboard.stats.growth', value: '+24.5%', color: 'primary' },
            { icon: Globe, label: 'dashboard.stats.monitored', value: '1.2M+', color: 'secondary' },
            { icon: DollarSign, label: 'dashboard.stats.value', value: '$5.2B', color: 'accent' },
            { icon: Shield, label: 'dashboard.stats.accuracy', value: '99.9%', color: 'destructive' },
          ].map((stat, i) => (
            <Card key={i} className="border-none shadow-soft-xl bg-card/50 backdrop-blur-sm hover:-translate-y-1 transition-transform duration-300">
              <CardContent className="p-8 text-center">
                <div className={`mx-auto w-12 h-12 rounded-2xl bg-${stat.color}/10 flex items-center justify-center mb-4`}>
                  <stat.icon className={`h-6 w-6 text-${stat.color}`} />
                </div>
                <div className="text-3xl font-bold text-foreground mb-1">{stat.value}</div>
                <div className="text-sm font-medium text-muted-foreground">{t(stat.label)}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Dashboard Section */}
        <div className="mb-16">
          <div className="flex items-center justify-between mb-10">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Cloud className="h-6 w-6 text-primary" />
              </div>
              <h2 className="text-3xl font-display font-bold text-foreground">
                Climate Dashboard
              </h2>
            </div>
            <PeriodButtons />
          </div>

          {/* Top Section - Location and Weather */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div className="hover:-translate-y-1 transition-transform duration-300">
              <LocationSelector />
            </div>
            <div className="hover:-translate-y-1 transition-transform duration-300">
              <WeatherWidget />
            </div>
          </div>

          {/* Interactive Map Section */}
          <div className="mb-8 hover:-translate-y-1 transition-transform duration-300">
            <MapDisplay />
          </div>

          {/* AI Insurance Recommendation */}
          <div className="mb-8 hover:-translate-y-1 transition-transform duration-300">
            <InsuranceRecommendation />
          </div>

          {/* Climate Data Analysis */}
          <div className="mb-8 hover:-translate-y-1 transition-transform duration-300">
            <ClimateDataWidget />
          </div>

          {/* Pricing Simulator */}
          <div className="mb-16 hover:-translate-y-1 transition-transform duration-300">
            <PricingSimulator />
          </div>
        </div>

        {/* Tokenization Section */}
        <div className="mb-12 rounded-3xl overflow-hidden relative shadow-2xl" id="tokenization-section">
          <div className="absolute inset-0 bg-gradient-ocean opacity-10"></div>
          <div className="relative p-12 md:p-16 flex flex-col md:flex-row items-center justify-between gap-12 bg-card/60 backdrop-blur-md">
            <div className="flex-1">
              <div className="inline-flex items-center gap-2 bg-primary/10 px-4 py-2 rounded-full mb-6">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold text-primary">Blockchain Powered</span>
              </div>
              <h2 className="text-3xl md:text-4xl font-display font-bold mb-4 text-foreground">
                Tokenização & Smart Contracts
              </h2>
              <p className="text-muted-foreground mb-8 text-lg leading-relaxed max-w-xl">
                Sistema avançado de tokenização de eventos climáticos e execução de contratos inteligentes com transparência total.
              </p>
              <Button
                onClick={() => window.location.href = '/tokenization'}
                size="lg"
                className="rounded-full px-8 shadow-lg shadow-primary/20"
              >
                <Zap className="mr-2 h-5 w-5" />
                Acessar Tokenização
              </Button>
            </div>
            <div className="hidden md:block relative">
              {/* Abstract decorative element */}
              <div className="w-64 h-64 bg-gradient-primary rounded-full opacity-20 blur-3xl absolute -top-10 -right-10 animate-pulse-slow"></div>
              <div className="relative z-10 bg-card p-6 rounded-2xl shadow-soft-lg border border-border/50">
                <Coins className="h-24 w-24 text-primary" />
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center py-20 bg-muted/30 rounded-3xl">
          <div className="max-w-3xl mx-auto px-4">
            <h3 className="text-4xl font-display font-bold text-foreground mb-6">
              Ready to Transform Climate Risk?
            </h3>
            <p className="text-xl text-muted-foreground mb-10 font-light">
              Join thousands of users leveraging ClimateWise for advanced climate analytics and risk management
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                className="rounded-full px-10 h-14 text-lg shadow-xl hover:scale-105 transition-all"
              >
                <Sparkles className="mr-2 h-5 w-5" />
                Get Started
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="rounded-full px-10 h-14 text-lg border-2 bg-background hover:bg-muted/50 hover:scale-105 transition-all"
              >
                <Globe className="mr-2 h-5 w-5" />
                Schedule Demo
              </Button>
            </div>
          </div>
        </div>
      </section>
    </DashboardLayout>
  );
}
