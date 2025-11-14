import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState, useEffect } from 'react';
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Package,
  Activity,
  PieChart,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Eye,
  Send,
  Download,
  AlertCircle
} from "lucide-react";
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1/blockchain';

interface TokenBalance {
  tokenUid: string;
  symbol: string;
  name: string;
  balance: number;
  value: number;
  change24h: number;
  eventType: string;
  severity: number;
  location: string;
  createdAt: string;
}

interface Transaction {
  id: string;
  type: 'mint' | 'transfer' | 'burn';
  tokenSymbol: string;
  amount: number;
  from: string;
  to: string;
  timestamp: string;
  status: 'confirmed' | 'pending' | 'failed';
  value: number;
}

interface WalletStats {
  totalTokens: number;
  totalValue: number;
  totalTransactions: number;
  portfolioChange24h: number;
  activeTokens: number;
}

export function TokenWalletMonitor() {
  const [walletAddress] = useState('climateai_wallet_001');
  const [stats, setStats] = useState<WalletStats>({
    totalTokens: 0,
    totalValue: 0,
    totalTransactions: 0,
    portfolioChange24h: 0,
    activeTokens: 0
  });
  const [balances, setBalances] = useState<TokenBalance[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);

  // Mock data - em produção, isso viria da API
  useEffect(() => {
    loadWalletData();
  }, []);

  const loadWalletData = async () => {
    setLoading(true);
    try {
      // Fazer chamadas reais para a API
      const [balanceResponse, transactionsResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/wallet/${walletAddress}/balance`),
        axios.get(`${API_BASE_URL}/wallet/${walletAddress}/transactions`)
      ]);

      const balanceData = balanceResponse.data;
      const transactionsData = transactionsResponse.data;

      // Atualizar estatísticas
      setStats({
        totalTokens: balanceData.total_tokens,
        totalValue: balanceData.total_value,
        totalTransactions: transactionsData.total_transactions,
        portfolioChange24h: balanceData.portfolio_change_24h,
        activeTokens: balanceData.active_tokens
      });

      // Atualizar saldos dos tokens
      setBalances(balanceData.tokens);

      // Atualizar transações
      setTransactions(transactionsData.transactions);

    } catch (error) {
      console.error('Erro ao carregar dados da carteira:', error);
      setError('Erro ao carregar dados da carteira. Verifique se o servidor está rodando.');
    } finally {
      setLoading(false);
    }
  };

  const getEventTypeColor = (type: string) => {
    const colors = {
      'enchente': 'bg-blue-500',
      'seca': 'bg-yellow-500',
      'onda_calor': 'bg-red-500',
      'geada': 'bg-purple-500',
      'seca_flash': 'bg-orange-500'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500';
  };

  const getSeverityColor = (severity: number) => {
    if (severity >= 4) return 'text-red-600';
    if (severity >= 3) return 'text-orange-600';
    if (severity >= 2) return 'text-yellow-600';
    return 'text-green-600';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-8">
      {/* Header com gradiente avançado */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 p-8 text-white">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl"></div>

        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-white/10 backdrop-blur-sm rounded-2xl border border-white/20">
              <Wallet className="h-10 w-10 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
                Climate Token Exchange
              </h1>
              <p className="text-blue-200 mt-1">Dashboard profissional de tokens climáticos</p>
              <div className="flex items-center gap-2 mt-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-400">Conectado à Blockchain ClimateAI</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm text-blue-200">Carteira</p>
              <p className="text-lg font-semibold">{walletAddress.slice(0, 12)}...{walletAddress.slice(-8)}</p>
            </div>
            <Button
              onClick={loadWalletData}
              disabled={loading}
              className="bg-white/10 hover:bg-white/20 border border-white/20 backdrop-blur-sm"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards com design premium */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="relative overflow-hidden border-0 shadow-xl bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -mr-10 -mt-10"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm font-medium">Total de Tokens</p>
                <p className="text-3xl font-bold mt-1">{stats.totalTokens}</p>
                <p className="text-blue-200 text-xs mt-1">Tokens ativos na carteira</p>
              </div>
              <div className="p-3 bg-white/20 rounded-xl">
                <Package className="h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden border-0 shadow-xl bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
          <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -mr-10 -mt-10"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-emerald-100 text-sm font-medium">Valor Total</p>
                <p className="text-3xl font-bold mt-1">{formatCurrency(stats.totalValue)}</p>
                <div className="flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 text-emerald-200 mr-1" />
                  <span className="text-emerald-200 text-xs">+{stats.portfolioChange24h}% 24h</span>
                </div>
              </div>
              <div className="p-3 bg-white/20 rounded-xl">
                <DollarSign className="h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden border-0 shadow-xl bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -mr-10 -mt-10"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm font-medium">Transações</p>
                <p className="text-3xl font-bold mt-1">{stats.totalTransactions}</p>
                <p className="text-purple-200 text-xs mt-1">Total realizadas</p>
              </div>
              <div className="p-3 bg-white/20 rounded-xl">
                <Activity className="h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden border-0 shadow-xl bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -mr-10 -mt-10"></div>
          <CardContent className="p-6 relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100 text-sm font-medium">Tokens Ativos</p>
                <p className="text-3xl font-bold mt-1">{stats.activeTokens}</p>
                <p className="text-orange-200 text-xs mt-1">Com saldo positivo</p>
              </div>
              <div className="p-3 bg-white/20 rounded-xl">
                <BarChart3 className="h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="portfolio" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="portfolio" className="flex items-center gap-2">
            <PieChart className="h-4 w-4" />
            Portfólio
          </TabsTrigger>
          <TabsTrigger value="transactions" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Transações
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Portfolio Tab */}
        <TabsContent value="portfolio" className="space-y-6">
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Tokens Climáticos
              </CardTitle>
              <CardDescription>
                Seus tokens representando eventos climáticos tokenizados
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {balances.map((token) => (
                  <Card key={token.tokenUid} className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-4">
                          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-white font-bold text-lg shadow-lg ${getEventTypeColor(token.eventType)}`}>
                            {token.symbol.slice(0, 2)}
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-gray-800">{token.symbol}</h3>
                            <p className="text-gray-600 text-sm mb-2">{token.name}</p>
                            <div className="flex items-center gap-2">
                              <Badge className={`${getEventTypeColor(token.eventType)} text-white border-0`}>
                                {token.eventType.toUpperCase()}
                              </Badge>
                              <Badge variant="outline" className={getSeverityColor(token.severity)}>
                                Nível {token.severity}
                              </Badge>
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="flex items-center gap-2 mb-1">
                            <div className={`w-3 h-3 rounded-full ${token.change24h >= 0 ? 'bg-green-500' : 'bg-red-500'}`}></div>
                            <span className={`text-sm font-semibold ${token.change24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {token.change24h >= 0 ? '+' : ''}{token.change24h}%
                            </span>
                          </div>
                          <p className="text-xs text-gray-500">24h</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div className="bg-blue-50 rounded-lg p-3">
                          <p className="text-xs text-blue-600 font-medium">Saldo</p>
                          <p className="text-lg font-bold text-blue-800">{token.balance.toLocaleString()}</p>
                          <p className="text-xs text-blue-600">tokens</p>
                        </div>
                        <div className="bg-green-50 rounded-lg p-3">
                          <p className="text-xs text-green-600 font-medium">Valor</p>
                          <p className="text-lg font-bold text-green-800">{formatCurrency(token.value)}</p>
                          <p className="text-xs text-green-600">estimado</p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                        <span>📍 {token.location}</span>
                        <span>📅 {new Date(token.createdAt).toLocaleDateString('pt-BR')}</span>
                      </div>

                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" className="flex-1 hover:bg-blue-50">
                          <Eye className="h-4 w-4 mr-2" />
                          Detalhes
                        </Button>
                        <Button variant="outline" size="sm" className="flex-1 hover:bg-purple-50">
                          <Send className="h-4 w-4 mr-2" />
                          Transferir
                        </Button>
                        <Button variant="outline" size="sm" className="hover:bg-green-50">
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="space-y-6">
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Histórico de Transações
              </CardTitle>
              <CardDescription>
                Todas as transações realizadas com seus tokens climáticos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {transactions.map((tx) => (
                  <Card key={tx.id} className="border-0 shadow-md hover:shadow-lg transition-all duration-300">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl shadow-lg ${
                            tx.type === 'mint' ? 'bg-gradient-to-br from-green-400 to-green-600 text-white' :
                            tx.type === 'transfer' ? 'bg-gradient-to-br from-blue-400 to-blue-600 text-white' :
                            'bg-gradient-to-br from-red-400 to-red-600 text-white'
                          }`}>
                            {tx.type === 'mint' ? '🪙' : tx.type === 'transfer' ? '↗️' : '🔥'}
                          </div>
                          <div>
                            <h3 className="font-bold text-gray-800 capitalize text-lg">{tx.type}</h3>
                            <p className="text-gray-600 font-medium">{tx.tokenSymbol}</p>
                            <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                              <span>📅 {formatDate(tx.timestamp)}</span>
                              <Badge variant={tx.status === 'confirmed' ? 'default' : 'secondary'} className="text-xs">
                                {tx.status === 'confirmed' ? '✅ Confirmado' : tx.status}
                              </Badge>
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-2xl font-bold text-gray-800">{tx.amount.toLocaleString()}</span>
                            <span className="text-gray-600">tokens</span>
                          </div>
                          <p className="text-sm text-gray-600">{formatCurrency(tx.value)}</p>
                          <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
                            <span>{tx.from === 'system' ? 'Sistema' : `${tx.from.slice(0, 6)}...${tx.from.slice(-4)}`}</span>
                            <span>→</span>
                            <span>{`${tx.to.slice(0, 6)}...${tx.to.slice(-4)}`}</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  Distribuição por Tipo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {['enchente', 'seca', 'onda_calor', 'geada'].map((type) => {
                    const count = balances.filter(b => b.eventType === type).length;
                    const percentage = balances.length > 0 ? (count / balances.length) * 100 : 0;
                    return (
                      <div key={type} className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-50 to-white rounded-lg border">
                        <div className="flex items-center gap-3">
                          <div className={`w-4 h-4 rounded-full ${getEventTypeColor(type)}`} />
                          <span className="capitalize font-medium text-gray-800">{type}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <Progress value={percentage} className="w-24" />
                          <span className="text-sm font-bold text-gray-700">{count} tokens</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Performance por Token
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {balances
                    .sort((a, b) => b.change24h - a.change24h)
                    .map((token) => (
                    <div key={token.tokenUid} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-800">{token.symbol}</p>
                        <p className="text-sm text-gray-600">{token.name.slice(0, 30)}...</p>
                      </div>
                      <div className={`flex items-center gap-1 font-semibold ${
                        token.change24h >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {token.change24h >= 0 ? (
                          <ArrowUpRight className="h-4 w-4" />
                        ) : (
                          <ArrowDownRight className="h-4 w-4" />
                        )}
                        {Math.abs(token.change24h)}%
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}