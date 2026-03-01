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
import { useTranslation } from "@/hooks/useTranslation";

interface ExecutiveDashboardProps {
    policySimulations: any[];
    financialAnalysis: any;
}

export const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
    policySimulations,
    financialAnalysis
}) => {
    const { t, language } = useTranslation();
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
                    <h2 className="text-2xl font-bold text-gray-900">{t('executive.title')}</h2>
                    <p className="text-gray-600">{t('executive.description')}</p>
                </div>
                <div className="flex items-center gap-2">
                    <select
                        value={selectedTimeframe}
                        onChange={(e) => setSelectedTimeframe(e.target.value as any)}
                        className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                        <option value="1M">{t('executive.timeframe.1M')}</option>
                        <option value="3M">{t('executive.timeframe.3M')}</option>
                        <option value="6M">{t('executive.timeframe.6M')}</option>
                        <option value="1Y">{t('executive.timeframe.1Y')}</option>
                    </select>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{t('executive.kpi.totalPremium')}</CardTitle>
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {t('common.currency')} {kpis.totalPremium.toLocaleString(language, { maximumFractionDigits: 0 })}
                        </div>
                        <div className="flex items-center text-xs text-green-600">
                            <TrendingUp className="h-3 w-3 mr-1" />
                            +{premiumVolumeChange}% {t('executive.kpi.vsPrevious')}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{t('executive.kpi.profitMargin')}</CardTitle>
                        <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {kpis.averageProfitMargin.toLocaleString(language, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
                        </div>
                        <div className="flex items-center text-xs text-green-600">
                            <TrendingUp className="h-3 w-3 mr-1" />
                            +{profitMarginChange}% {t('executive.kpi.vsPrevious')}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{t('executive.kpi.riskAdjustedReturn')}</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {kpis.riskAdjustedReturn.toLocaleString(language, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}x
                        </div>
                        <div className="text-xs text-gray-600">
                            {t('executive.kpi.portfolioAverage')}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{t('executive.kpi.profitablePolicies')}</CardTitle>
                        <Shield className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {kpis.profitablePolicies}/{kpis.totalPolicies}
                        </div>
                        <div className="text-xs text-gray-600">
                            {((kpis.profitablePolicies / kpis.totalPolicies) * 100).toLocaleString(language, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}% {t('executive.kpi.portfolioPercentage')}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Risk Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">{t('executive.risk.title')}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">{t('executive.risk.totalExpectedLoss')}:</span>
                            <span className="font-bold text-red-600">
                                {t('common.currency')} {kpis.totalExpectedLoss.toLocaleString(language, { maximumFractionDigits: 0 })}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">{t('executive.risk.lossPremiumRatio')}:</span>
                            <span className="font-bold">
                                {((kpis.totalExpectedLoss / kpis.totalPremium) * 100).toLocaleString(language, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">{t('executive.risk.capitalRequirement')}:</span>
                            <span className="font-bold text-blue-600">
                                {financialAnalysis?.insurerAnalysis?.capitalRequirement ? `${t('common.currency')} ${financialAnalysis.insurerAnalysis.capitalRequirement.toLocaleString(language, { maximumFractionDigits: 0 })}` : 'N/A'}
                            </span>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">{t('executive.alerts.title')}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {kpis.averageProfitMargin < 10 && (
                            <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded">
                                <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
                                <div>
                                    <div className="text-sm font-medium text-yellow-800">{t('executive.alerts.lowMargin.title')}</div>
                                    <div className="text-xs text-yellow-700">
                                        {t('executive.alerts.lowMargin.desc')}
                                    </div>
                                </div>
                            </div>
                        )}

                        {financialAnalysis?.riskAnalysis?.reinsuranceNeed && (
                            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded">
                                <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                                <div>
                                    <div className="text-sm font-medium text-red-800">{t('executive.alerts.reinsurance.title')}</div>
                                    <div className="text-xs text-red-700">
                                        {t('executive.alerts.reinsurance.desc')}
                                    </div>
                                </div>
                            </div>
                        )}

                        {kpis.profitablePolicies / kpis.totalPolicies < 0.7 && (
                            <div className="flex items-start gap-2 p-3 bg-orange-50 border border-orange-200 rounded">
                                <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5" />
                                <div>
                                    <div className="text-sm font-medium text-orange-800">{t('executive.alerts.lowProfitability.title')}</div>
                                    <div className="text-xs text-orange-700">
                                        {t('executive.alerts.lowProfitability.desc')}
                                    </div>
                                </div>
                            </div>
                        )}

                        {kpis.profitablePolicies / kpis.totalPolicies >= 0.8 && (
                            <div className="flex items-start gap-2 p-3 bg-green-50 border border-green-200 rounded">
                                <TrendingUp className="h-4 w-4 text-green-600 mt-0.5" />
                                <div>
                                    <div className="text-sm font-medium text-green-800">{t('executive.alerts.healthy.title')}</div>
                                    <div className="text-xs text-green-700">
                                        {t('executive.alerts.healthy.desc')}
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
                    <CardTitle className="text-lg">{t('executive.performance.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {policySimulations.map((sim, index) => (
                            <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                        <h4 className="font-medium">{sim.name}</h4>
                                        <Badge variant={sim.isViable ? "default" : "danger"}>
                                            {sim.isViable ? t('executive.performance.viable') : t('executive.performance.notViable')}
                                        </Badge>
                                    </div>
                                    <p className="text-sm text-gray-600 mt-1">{sim.description}</p>
                                </div>
                                <div className="text-right">
                                    <div className="text-lg font-bold">
                                        {t('common.currency')} {sim.premium.toLocaleString(language, { maximumFractionDigits: 0 })}
                                    </div>
                                    <div className="text-sm text-gray-600">
                                        {t('executive.kpi.margin', { margin: sim.profitMarginPercentage.toLocaleString(language, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) })}
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