import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, Cloud, CloudRain, Sun, Wind, Thermometer, Droplets, Zap, TrendingUp, Shield, Globe, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "@/hooks/useTranslation";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useEffect, useState } from "react";

// Animated weather particle component
function WeatherParticle({ type, delay }: { type: 'rain' | 'cloud' | 'wind', delay: number }) {
  const baseClass = "absolute pointer-events-none";

  if (type === 'rain') {
    return (
      <div
        className={`${baseClass} w-0.5 h-8 bg-gradient-to-b from-blue-400 to-transparent opacity-40`}
        style={{
          left: `${Math.random() * 100}%`,
          top: '-2rem',
          animation: `rainFall ${2 + Math.random() * 2}s linear infinite`,
          animationDelay: `${delay}s`
        }}
      />
    );
  }

  if (type === 'cloud') {
    return (
      <div
        className={`${baseClass} text-white/20 text-4xl`}
        style={{
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 30}%`,
          animation: `cloudFloat ${15 + Math.random() * 10}s linear infinite`,
          animationDelay: `${delay}s`
        }}
      >
        ☁️
      </div>
    );
  }

  if (type === 'wind') {
    return (
      <div
        className={`${baseClass} w-12 h-0.5 bg-gradient-to-r from-transparent via-cyan-300/30 to-transparent`}
        style={{
          left: '-3rem',
          top: `${Math.random() * 100}%`,
          animation: `windBlow ${3 + Math.random() * 2}s linear infinite`,
          animationDelay: `${delay}s`
        }}
      />
    );
  }

  return null;
}

// Dynamic temperature display
function TemperatureDisplay() {
  const [temp, setTemp] = useState(22);

  useEffect(() => {
    const interval = setInterval(() => {
      setTemp(prev => {
        const change = (Math.random() - 0.5) * 2;
        const newTemp = prev + change;
        return Math.max(15, Math.min(35, newTemp));
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const tempColor = temp > 28 ? 'from-orange-500 to-red-500' :
    temp > 22 ? 'from-yellow-500 to-orange-500' :
      'from-cyan-500 to-blue-500';

  return (
    <div className="absolute top-24 right-8 glass-card px-6 py-4 rounded-2xl border-0 shadow-xl z-40">
      <div className="flex items-center gap-3">
        <Thermometer className={`h-8 w-8 bg-gradient-to-br ${tempColor} bg-clip-text text-transparent`} style={{ WebkitTextFillColor: 'transparent' }} />
        <div>
          <div className={`text-3xl font-black bg-gradient-to-r ${tempColor} bg-clip-text text-transparent`}>
            {temp.toFixed(1)}°C
          </div>
          <div className="text-xs text-muted-foreground font-medium">Live Climate Data</div>
        </div>
      </div>
    </div>
  );
}

export function WelcomePage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [weatherMode, setWeatherMode] = useState<'sunny' | 'rainy' | 'cloudy'>('sunny');

  useEffect(() => {
    // Cycle through weather modes
    const modes: Array<'sunny' | 'rainy' | 'cloudy'> = ['sunny', 'rainy', 'cloudy'];
    let index = 0;

    const interval = setInterval(() => {
      index = (index + 1) % modes.length;
      setWeatherMode(modes[index]);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const features = [
    {
      icon: <TrendingUp className="h-8 w-8" />,
      title: t('feature.analysis.title'),
      description: t('feature.analysis.desc'),
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: <Shield className="h-8 w-8" />,
      title: t('feature.actuarial.title'),
      description: t('feature.actuarial.desc'),
      gradient: 'from-emerald-500 to-teal-500'
    },
    {
      icon: <Zap className="h-8 w-8" />,
      title: t('feature.dashboard.title'),
      description: t('feature.dashboard.desc'),
      gradient: 'from-purple-500 to-pink-500'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 relative overflow-hidden">
      {/* Animated CSS Keyframes */}
      <style>{`
        @keyframes rainFall {
          from { transform: translateY(0); }
          to { transform: translateY(100vh); }
        }

        @keyframes cloudFloat {
          from { transform: translateX(-100%); }
          to { transform: translateX(calc(100vw + 100%)); }
        }

        @keyframes windBlow {
          from { transform: translateX(0); }
          to { transform: translateX(100vw); }
        }

        @keyframes sunPulse {
          0%, 100% { transform: scale(1); opacity: 0.8; }
          50% { transform: scale(1.1); opacity: 1; }
        }

        @keyframes rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      {/* Dynamic Weather Effects */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Sun (always present, different opacity) */}
        <div
          className={`absolute top-12 right-20 w-32 h-32 rounded-full bg-gradient-to-br from-yellow-300 to-orange-400 blur-2xl transition-opacity duration-1000 ${weatherMode === 'sunny' ? 'opacity-80' : 'opacity-20'
            }`}
          style={{ animation: 'sunPulse 4s ease-in-out infinite' }}
        />

        {/* Sun rays */}
        {weatherMode === 'sunny' && (
          <div className="absolute top-12 right-20 w-32 h-32">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="absolute top-1/2 left-1/2 w-1 h-20 bg-gradient-to-t from-yellow-400/40 to-transparent origin-top"
                style={{
                  transform: `translate(-50%, -50%) rotate(${i * 45}deg)`,
                  animation: 'rotate 20s linear infinite'
                }}
              />
            ))}
          </div>
        )}

        {/* Rain particles */}
        {weatherMode === 'rainy' && (
          <>
            {[...Array(30)].map((_, i) => (
              <WeatherParticle key={`rain-${i}`} type="rain" delay={i * 0.1} />
            ))}
          </>
        )}

        {/* Clouds */}
        {(weatherMode === 'cloudy' || weatherMode === 'rainy') && (
          <>
            {[...Array(5)].map((_, i) => (
              <WeatherParticle key={`cloud-${i}`} type="cloud" delay={i * 3} />
            ))}
          </>
        )}

        {/* Wind particles */}
        {[...Array(6)].map((_, i) => (
          <WeatherParticle key={`wind-${i}`} type="wind" delay={i * 0.5} />
        ))}

        {/* Floating gradient orbs */}
        <div className="absolute -bottom-20 -left-20 w-96 h-96 bg-cyan-400/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/3 -right-20 w-80 h-80 bg-blue-400/20 rounded-full blur-3xl animate-pulse animation-delay-500" />
        <div className="absolute bottom-1/4 left-1/3 w-64 h-64 bg-emerald-400/20 rounded-full blur-3xl animate-pulse animation-delay-300" />
      </div>

      {/* Temperature Display */}
      <TemperatureDisplay />

      {/* Header */}
      <header className="glass-card sticky top-0 z-50 border-b-0 shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg glow">
                <span className="text-white font-black text-lg">CA</span>
              </div>
              <span className="text-2xl font-black bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
                {t('app.name')}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <LanguageSwitcher />
              <Button
                onClick={() => navigate('/auth')}
                className="btn-premium shadow-xl"
              >
                {t('nav.login')} / {t('nav.signup')}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-24 px-4 relative z-10">
        <div className="container mx-auto max-w-5xl text-center">
          <div className="mb-12">
            {/* Animated weather icon based on mode */}
            <div className="mb-8 relative inline-block">
              {weatherMode === 'sunny' && (
                <Sun className="h-20 w-20 text-yellow-500 mx-auto animate-pulse" />
              )}
              {weatherMode === 'rainy' && (
                <CloudRain className="h-20 w-20 text-blue-500 mx-auto" />
              )}
              {weatherMode === 'cloudy' && (
                <Cloud className="h-20 w-20 text-slate-400 mx-auto float" />
              )}
              <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-full blur-xl -z-10" />
            </div>

            <h1 className="text-5xl md:text-7xl font-black text-gray-900 mb-8 leading-tight">
              {t('hero.welcome')}{' '}
              <span className="relative inline-block">
                <span className="gradient-text">{t('app.name')}</span>
                <Sparkles className="absolute -top-6 -right-6 h-8 w-8 text-yellow-500 animate-pulse" />
              </span>
            </h1>

            <p className="text-2xl text-gray-700 mb-10 max-w-3xl mx-auto font-light leading-relaxed">
              {t('hero.description')}
            </p>
          </div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {features.map((feature, index) => (
              <Card
                key={index}
                className="glass-card border-0 shadow-xl hover-lift group overflow-hidden"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity`} />
                <CardHeader className="relative">
                  <div className={`mx-auto mb-4 p-4 rounded-2xl bg-gradient-to-br ${feature.gradient} shadow-lg glow-green`}>
                    <div className="text-white">
                      {feature.icon}
                    </div>
                  </div>
                  <CardTitle className="text-xl font-bold">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent className="relative">
                  <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* CTA */}
          <div className="space-y-6">
            <Button
              size="lg"
              onClick={() => navigate('/dashboard')}
              className="btn-premium text-xl px-12 py-8 shadow-2xl"
            >
              <Globe className="mr-3 h-6 w-6" />
              {t('hero.cta')}
              <ArrowRight className="ml-3 h-6 w-6" />
            </Button>
            <p className="text-gray-500 text-lg font-medium">
              {t('hero.subtitle')}
            </p>
          </div>
        </div>
      </section>

      {/* Weather Mode Indicator */}
      <div className="fixed bottom-8 left-8 z-50">
        <div className="glass-card px-6 py-3 rounded-full border-0 shadow-xl flex items-center gap-3">
          {weatherMode === 'sunny' && <Sun className="h-5 w-5 text-yellow-500" />}
          {weatherMode === 'rainy' && <CloudRain className="h-5 w-5 text-blue-500" />}
          {weatherMode === 'cloudy' && <Cloud className="h-5 w-5 text-slate-500" />}
          <span className="text-sm font-semibold capitalize text-gray-700">
            {weatherMode} Mode
          </span>
        </div>
      </div>

      {/* Quick Start Guide */}
      <section className="py-20 relative z-10">
        <div className="absolute inset-0 bg-white/30 backdrop-blur-sm" />
        <div className="container mx-auto max-w-5xl px-4 relative">
          <h2 className="text-4xl font-black text-center mb-16 bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
            {t('guide.title')}
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              { step: 1, color: 'blue', icon: <Globe className="h-6 w-6" /> },
              { step: 2, color: 'emerald', icon: <TrendingUp className="h-6 w-6" /> },
              { step: 3, color: 'purple', icon: <Zap className="h-6 w-6" /> },
              { step: 4, color: 'orange', icon: <Droplets className="h-6 w-6" /> }
            ].map(({ step, color, icon }) => (
              <Card key={step} className="glass-card border-0 shadow-xl hover-lift group">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <div className={`bg-gradient-to-br from-${color}-500 to-${color}-600 text-white rounded-xl w-12 h-12 flex items-center justify-center shadow-lg font-black text-lg`}>
                      {step}
                    </div>
                    <div className="flex-1">
                      <div className="font-black text-lg">{t(`guide.step${step}.title`)}</div>
                    </div>
                    <div className={`text-${color}-500 opacity-50 group-hover:opacity-100 transition-opacity`}>
                      {icon}
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 leading-relaxed">
                    {t(`guide.step${step}.desc`)}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gradient-to-r from-slate-900 to-blue-900 text-white py-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjA1IiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-50" />
        <div className="container mx-auto px-4 text-center relative">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Wind className="h-6 w-6 text-cyan-400" />
            <p className="text-gray-300 text-lg font-medium">
              {t('footer.copyright')}
            </p>
            <Droplets className="h-6 w-6 text-blue-400" />
          </div>
          <p className="text-cyan-400 text-sm font-semibold">
            Powered by Advanced Climate Intelligence
          </p>
        </div>
      </footer>
    </div>
  );
}
