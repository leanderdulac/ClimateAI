import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, CheckCircle, TrendingUp, Shield, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function WelcomePage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: <TrendingUp className="h-8 w-8 text-blue-600" />,
      title: "Análise Climática Avançada",
      description: "Modelos de IA para previsão de riscos climáticos e impacto econômico"
    },
    {
      icon: <Shield className="h-8 w-8 text-green-600" />,
      title: "Modelagem Atuarial",
      description: "Cálculos precisos de prêmios baseados em dados climáticos históricos"
    },
    {
      icon: <Zap className="h-8 w-8 text-purple-600" />,
      title: "Dashboard Interativo",
      description: "Interface intuitiva para visualização de dados e tomada de decisões"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-green-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">CA</span>
              </div>
              <span className="text-xl font-bold text-gray-900">ClimateAI</span>
            </div>
            <Button
              onClick={() => navigate('/auth')}
              className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700"
            >
              Entrar / Cadastrar
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <div className="mb-8">
            <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Bem-vindo ao <span className="bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">ClimateAI</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Você chegou ao futuro da modelagem climático-econômica. Nossa plataforma combina inteligência artificial,
              dados climáticos e modelagem atuarial para ajudar você a tomar decisões mais inteligentes.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {features.map((feature, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="mx-auto mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="space-y-4">
            <Button
              size="lg"
              onClick={() => navigate('/dashboard')}
              className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 text-white px-8 py-4 text-lg"
            >
              Começar a Explorar
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <p className="text-gray-500">
              Descubra como transformar riscos climáticos em oportunidades
            </p>
          </div>
        </div>
      </section>

      {/* Quick Start Guide */}
      <section className="py-16 bg-white/50">
        <div className="container mx-auto max-w-4xl px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Como Começar</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="bg-blue-100 text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</span>
                  Selecione uma Localização
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Escolha uma cidade ou região para analisar os dados climáticos e riscos associados.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="bg-green-100 text-green-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</span>
                  Configure o Período
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Defina o período de análise (7, 30 ou 90 dias) para obter previsões precisas.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="bg-purple-100 text-purple-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</span>
                  Visualize os Dados
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Explore gráficos interativos, mapas de risco e métricas de performance.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="bg-orange-100 text-orange-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">4</span>
                  Simule Cenários
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Use nossa calculadora atuarial para simular diferentes cenários de risco.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-400">
            © 2024 ClimateAI. Transformando riscos climáticos em oportunidades.
          </p>
        </div>
      </footer>
    </div>
  );
}
