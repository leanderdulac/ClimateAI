import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { LocationSelector } from "@/components/LocationSelector";
import { WeatherWidget } from "@/components/WeatherWidget";
import { PricingSimulator } from "@/components/PricingSimulator";
import { ClimateEventTokenizer } from "@/components/ClimateEventTokenizer";
import { SmartContractMonitor } from "@/components/SmartContractMonitor";
import { LocationProvider } from "@/lib/LocationContext";
import { PeriodProvider, usePeriod } from "@/lib/PeriodContext";
import { Globe, TrendingUp, DollarSign, Zap, Cloud } from "lucide-react";

function PeriodButtons() {
  const { selectedPeriod, setSelectedPeriod } = usePeriod();

  return (
    <div className="ml-auto flex gap-2">
      <Button
        variant={selectedPeriod === 7 ? "default" : "outline"}
        size="sm"
        onClick={() => setSelectedPeriod(7)}
      >
        7D
      </Button>
      <Button
        variant={selectedPeriod === 30 ? "default" : "outline"}
        size="sm"
        onClick={() => setSelectedPeriod(30)}
      >
        30D
      </Button>
      <Button
        variant={selectedPeriod === 90 ? "default" : "outline"}
        size="sm"
        onClick={() => setSelectedPeriod(90)}
      >
        90D
      </Button>
    </div>
  );
}

export function IndexPage() {
  const isDemoMode = !import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL === '';
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Banner de Modo Demo */}
      {isDemoMode && (
        <div className="bg-amber-500 text-white py-2 px-4 text-center text-sm">
          <span className="font-medium">⚠️ Modo Demo:</span> Exibindo dados simulados. Configure VITE_API_BASE_URL para conectar ao backend real.
        </div>
      )}
      
      {/* Hero Section */}
      <section className="py-16 md:py-24 bg-gradient-to-r from-blue-900/10 to-green-900/10">
        <div className="container mx-auto max-w-7xl px-4">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-blue-100/20 px-4 py-2 rounded-full text-sm text-blue-800 mb-6">
              <Zap className="h-4 w-4" />
              Advanced Climate Analytics
            </div>
            <h1 className="text-5xl md:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-green-600 mb-6">
              ClimateWise 🌍
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-10 text-gray-700">
              A revolutionary platform for tokenizing and pricing climate events with advanced analytics and real-time monitoring
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white"
                onClick={() => {
                  const dashboard = document.querySelector('#dashboard');
                  if (dashboard) {
                    dashboard.scrollIntoView({ behavior: 'smooth' });
                  } else {
                    console.warn('Dashboard section not found');
                    // Fallback: scroll to ClimateDataWidget if it exists
                    const dataWidget = document.querySelector('.climate-data-widget');
                    dataWidget?.scrollIntoView({ behavior: 'smooth' });
                  }
                }}
              >
                Start Analysis
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-2 border-blue-200 text-blue-700 hover:bg-blue-50"
                onClick={() => {
                  const dataWidget = document.querySelector('.climate-data-widget');
                  if (dataWidget) {
                    dataWidget.scrollIntoView({ behavior: 'smooth' });
                  } else {
                    // Alternativa: Rolar até a seção de estatísticas
                    const statsSection = document.querySelector('.stats-section');
                    statsSection?.scrollIntoView({ behavior: 'smooth' });
                  }
                }}
              >
                Explore Data
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white stats-section">
        <div className="container mx-auto max-w-7xl px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-16">
            <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-50 to-blue-100">
              <CardContent className="p-6 text-center">
                <TrendingUp className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-blue-800">+24.5%</div>
                <div className="text-sm text-blue-600">Market Growth</div>
              </CardContent>
            </Card>
            <Card className="border-0 shadow-lg bg-gradient-to-br from-green-50 to-green-100">
              <CardContent className="p-6 text-center">
                <Globe className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-green-800">1.2M+</div>
                <div className="text-sm text-green-600">Climate Events Monitored</div>
              </CardContent>
            </Card>
            <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-50 to-purple-100">
              <CardContent className="p-6 text-center">
                <DollarSign className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-purple-800">$5.2B</div>
                <div className="text-sm text-purple-600">Tokenized Value</div>
              </CardContent>
            </Card>
            <Card className="border-0 shadow-lg bg-gradient-to-br from-orange-50 to-orange-100">
              <CardContent className="p-6 text-center">
                <Zap className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-orange-800">99.9%</div>
                <div className="text-sm text-orange-600">Prediction Accuracy</div>
              </CardContent>
            </Card>
          </div>

          {/* Main Dashboard Section */}
          <div className="mb-16">
            <PeriodProvider>
              <div className="flex items-center gap-3 mb-8">
                <Globe className="h-8 w-8 text-blue-600" />
                <h2 className="text-3xl font-bold text-gray-800">Climate Dashboard</h2>
                <PeriodButtons />
              </div>

              {/* Top Section - Location and Weather */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
                <LocationProvider>
                  <LocationSelector />
                  <WeatherWidget />
                </LocationProvider>
              </div>

              {/* Pricing Simulator - Full Width with More Space */}
              <div className="mb-16">
                <LocationProvider>
                  <PricingSimulator />
                </LocationProvider>
              </div>

              {/* Climate Event Tokenizer - Separate Section Below */}
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-6">
                  <Cloud className="h-6 w-6 text-orange-600" />
                  <h3 className="text-2xl font-semibold text-gray-800">Tokenização de Eventos Climáticos</h3>
                </div>
                <LocationProvider>
                  <ClimateEventTokenizer />
                </LocationProvider>
              </div>
            </PeriodProvider>
          </div>

          {/* Smart Contract Monitor Section */}
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-8">
              <Zap className="h-8 w-8 text-green-600" />
              <h2 className="text-3xl font-bold text-gray-800">Smart Contract Monitor</h2>
            </div>
            <SmartContractMonitor />
          </div>

          {/* CTA Section */}
          <div className="text-center py-12">
            <Card className="border-0 shadow-xl bg-gradient-to-r from-blue-600 to-green-600 text-white">
              <CardContent className="p-12">
                <h3 className="text-3xl font-bold mb-4">Ready to Transform Climate Risk?</h3>
                <p className="text-lg mb-8 max-w-2xl mx-auto opacity-90">
                  Join thousands of users leveraging ClimateWise for advanced climate analytics and risk management
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button size="lg" className="bg-white text-blue-600 hover:bg-blue-50">
                    Get Started
                  </Button>
                  <Button size="lg" variant="secondary" className="bg-transparent border-white text-white hover:bg-white/10">
                    Schedule Demo
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}