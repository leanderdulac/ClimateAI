import * as React from 'react';
const { useState } = React;
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import {
    TrendingUp,
    DollarSign,
    Shield,
    AlertTriangle,
    BarChart3,
    Activity
} from 'lucide-react';

interface ExecutiveDashboardProps {
    policySimulations: any[];
    financialAnalysis: any;
}

export const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
    policySimulations,
    financialAnalysis
}) => {
    const [selectedTimeframe, setSelectedTimeframe] = useState<'1M' | '3M' | '6M' | '1Y'>('3M');

    // Simulated real-time KPIs (in production, these would come from APIs)
    const kpis = {
        totalPremium: policySimulations.reduce((sum, sim) => sum + sim.premium, 0),
        totalExpectedLoss: policySimulations.reduce((sum, sim) => sum + sim.expectedLoss, 0),
        averageProfitMargin: policySimulations.reduce((sum, sim) => sum + sim.profitMarginPercentage, 0) / policySimulations.length,
        riskAdjustedReturn: policySimulations.reduce((sum, sim) => sum + sim.riskAdjustedReturn, 0) / policySimulations.length,
        profitablePolicies: policySimulations.filter(sim => sim.isViable).length,
        totalPolicies: policySimulations.length
    };

    const profitMarginChange = 2.5; // Simulated change percentage
    const premiumVolumeChange = 8.3; // Simulated change percentage

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Dashboard Executivo</h2>
                    <p className="text-gray-600">Visão geral das carteiras de seguros climáticos</p>
                </div>
                <div className="flex items-center gap-2">
                    <select
                        value={selectedTimeframe}
                        onChange={(e) => setSelectedTimeframe(e.target.value as any)}
                        className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                        <option value="1M">Último Mês</option>
                        <option value="3M">Últimos 3 Meses</option>
                        <option value="6M">Últimos 6 Meses</option>
                        <option value="1Y">Último Ano</option>
                    </select>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Volume Total de Prêmios</CardTitle>
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            R$ {kpis.totalPremium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                        <div className="flex items-center text-xs text-green-600">
                            <TrendingUp className="h-3 w-3 mr-1" />
                            +{premiumVolumeChange}% vs período anterior
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Margem de Lucro Média</CardTitle>
                        <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {kpis.averageProfitMargin.toFixed(1)}%
                        </div>
                        <div className="flex items-center text-xs text-green-600">
                            <TrendingUp className="h-3 w-3 mr-1" />
                            +{profitMarginChange}% vs período anterior
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Retorno Ajustado ao Risco</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {kpis.riskAdjustedReturn.toFixed(2)}x
                        </div>
                        <div className="text-xs text-gray-600">
                            Média da carteira
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Apólices Lucrativas</CardTitle>
                        <Shield className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {kpis.profitablePolicies}/{kpis.totalPolicies}
                        </div>
                        <div className="text-xs text-gray-600">
                            {((kpis.profitablePolicies / kpis.totalPolicies) * 100).toFixed(1)}% da carteira
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Risk Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Visão Geral de Riscos</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Perda Esperada Total:</span>
                            <span className="font-bold text-red-600">
                                R$ {kpis.totalExpectedLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Ratio Perda/Prêmio:</span>
                            <span className="font-bold">
                                {((kpis.totalExpectedLoss / kpis.totalPremium) * 100).toFixed(1)}%
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">Capital Necessário (VaR 99%):</span>
                            <span className="font-bold text-blue-600">
                                R$ {financialAnalysis?.insurerAnalysis?.capitalRequirement?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 'N/A'}
                            </span>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Alertas e Recomendações</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {kpis.averageProfitMargin < 10 && (
                            <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded">
                                <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
                                <div>
                                    <div className="text-sm font-medium text-yellow-800">Margem Baixa</div>
                                    <div className="text-xs text-yellow-700">
                                        Margem média abaixo de 10%. Considerar revisão de precificação.
                                    </div>
                                </div>
                            </div>
                        )}

                        {financialAnalysis?.riskAnalysis?.reinsuranceNeed && (
                            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded">
                                <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                                <div>
                                    <div className="text-sm font-medium text-red-800">Reinsurance Necessário</div>
                                    <div className="text-xs text-red-700">
                                        Requisito de capital elevado. Recomendado contratar reinsurance.
                                    </div>
                                </div>
                            </div>
                        )}

                        {kpis.profitablePolicies / kpis.totalPolicies < 0.7 && (
                            <div className="flex items-start gap-2 p-3 bg-orange-50 border border-orange-200 rounded">
                                <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5" />
                                <div>
                                    <div className="text-sm font-medium text-orange-800">Baixa Lucratividade</div>
                                    <div className="text-xs text-orange-700">
                                        Menos de 70% das apólices são lucrativas. Revisar underwriting.
                                    </div>
                                </div>
                            </div>
                        )}

                        {kpis.profitablePolicies / kpis.totalPolicies >= 0.8 && (
                            <div className="flex items-start gap-2 p-3 bg-green-50 border border-green-200 rounded">
                                <TrendingUp className="h-4 w-4 text-green-600 mt-0.5" />
                                <div>
                                    <div className="text-sm font-medium text-green-800">Carteira Saudável</div>
                                    <div className="text-xs text-green-700">
                                        Mais de 80% das apólices são lucrativas. Continue com estratégia atual.
                                    </div>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Performance by Configuration */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Performance por Configuração</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {policySimulations.map((sim, index) => (
                            <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                        <h4 className="font-medium">{sim.name}</h4>
                                        <Badge variant={sim.isViable ? "default" : "danger"}>
                                            {sim.isViable ? 'Viável' : 'Não Viável'}
                                        </Badge>
                                    </div>
                                    <p className="text-sm text-gray-600 mt-1">{sim.description}</p>
                                </div>
                                <div className="text-right">
                                    <div className="text-lg font-bold">
                                        R$ {sim.premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                    </div>
                                    <div className="text-sm text-gray-600">
                                        Margem: {sim.profitMarginPercentage.toFixed(1)}%
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};