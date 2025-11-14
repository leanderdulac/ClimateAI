import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useState } from 'react';
import { ClimateEventTokenizer } from "@/components/ClimateEventTokenizer";
import { TokenWalletMonitor } from "@/components/TokenWalletMonitor";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Zap,
  Package,
  TrendingUp,
  AlertTriangle,
  Thermometer,
  CloudRain,
  Wind,
  Waves,
  Snowflake,
  Sun,
  Coins,
  BarChart3,
  Plus,
  History
} from "lucide-react";

export function TokenizationPage() {
  const [activeTab, setActiveTab] = useState("create");

  return (
    <DashboardLayout
      title="Tokenização Climática"
      subtitle="Transforme eventos climáticos em ativos tokenizados"
    >
      {/* Stats Cards */}
      <div className="bg-gradient-to-r from-blue-900 via-purple-900 to-green-900 text-white">
        <div className="container mx-auto px-6 py-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <CloudRain className="h-8 w-8 text-blue-300" />
                <h3 className="text-lg font-semibold">Eventos</h3>
              </div>
              <p className="text-3xl font-bold">1,247</p>
              <p className="text-blue-200 text-sm">Eventos monitorados</p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <Coins className="h-8 w-8 text-yellow-300" />
                <h3 className="text-lg font-semibold">Tokens</h3>
              </div>
              <p className="text-3xl font-bold">89</p>
              <p className="text-blue-200 text-sm">Tokens criados</p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <TrendingUp className="h-8 w-8 text-green-300" />
                <h3 className="text-lg font-semibold">Volume</h3>
              </div>
              <p className="text-3xl font-bold">R$ 2.4M</p>
              <p className="text-blue-200 text-sm">Valor tokenizado</p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <BarChart3 className="h-8 w-8 text-purple-300" />
                <h3 className="text-lg font-semibold">Ativos</h3>
              </div>
              <p className="text-3xl font-bold">156</p>
              <p className="text-blue-200 text-sm">Carteiras ativas</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-12">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
          <TabsList className="grid w-full grid-cols-3 lg:w-auto lg:grid-cols-none lg:flex">
            <TabsTrigger value="create" className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Criar Token
            </TabsTrigger>
            <TabsTrigger value="portfolio" className="flex items-center gap-2">
              <Package className="h-4 w-4" />
              Meu Portfólio
            </TabsTrigger>
            <TabsTrigger value="market" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Mercado
            </TabsTrigger>
          </TabsList>

          <TabsContent value="create" className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <ClimateEventTokenizer />
              </div>

              <div className="space-y-6">
                {/* Quick Stats */}
                <Card className="border-0 shadow-xl">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-5 w-5 text-yellow-600" />
                      Estatísticas Rápidas
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Tokens criados hoje</span>
                      <span className="font-semibold">3</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Valor médio</span>
                      <span className="font-semibold">R$ 35.000</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Taxa de sucesso</span>
                      <span className="font-semibold text-green-600">98.5%</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Event Types */}
                <Card className="border-0 shadow-xl">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-orange-600" />
                      Tipos de Eventos
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                      <Thermometer className="h-5 w-5 text-red-600" />
                      <div>
                        <p className="font-medium text-red-800">Onda de Calor</p>
                        <p className="text-sm text-red-600">Temperatura extrema</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                      <CloudRain className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium text-blue-800">Enchente</p>
                        <p className="text-sm text-blue-600">Precipitação excessiva</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                      <Sun className="h-5 w-5 text-yellow-600" />
                      <div>
                        <p className="font-medium text-yellow-800">Seca</p>
                        <p className="text-sm text-yellow-600">Falta de precipitação</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                      <Snowflake className="h-5 w-5 text-purple-600" />
                      <div>
                        <p className="font-medium text-purple-800">Geada</p>
                        <p className="text-sm text-purple-600">Temperatura muito baixa</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="portfolio" className="space-y-8">
            <TokenWalletMonitor />
          </TabsContent>

          <TabsContent value="market" className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card className="border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Mercado de Tokens Climáticos
                  </CardTitle>
                  <CardDescription>
                    Tokens disponíveis para negociação
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <p className="font-semibold">ENC425</p>
                        <p className="text-sm text-gray-600">Enchente - Porto Velho</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">R$ 1,00</p>
                        <p className="text-sm text-green-600">+12.5%</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <p className="font-semibold">SEC325</p>
                        <p className="text-sm text-gray-600">Seca - São Paulo</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">R$ 1,00</p>
                        <p className="text-sm text-red-600">-3.2%</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <p className="font-semibold">CAL425</p>
                        <p className="text-sm text-gray-600">Onda de Calor - Rio</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">R$ 1,00</p>
                        <p className="text-sm text-green-600">+25.8%</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5" />
                      Atividade Recente
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Novo token criado</p>
                        <p className="text-xs text-gray-600">ENC425 - 2 minutos atrás</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Transferência realizada</p>
                        <p className="text-xs text-gray-600">SEC325 - 15 minutos atrás</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Token liquidado</p>
                        <p className="text-xs text-gray-600">CAL425 - 1 hora atrás</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}