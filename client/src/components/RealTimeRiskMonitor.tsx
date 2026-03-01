import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { parametricApi, RealTimeRiskAnalysis } from '@/lib/parametricApi';
import { AlertTriangle, ShieldAlert, TrendingUp, Info, MapPin, DollarSign } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { useTranslation } from "@/hooks/useTranslation";

export function RealTimeRiskMonitor() {
    const { t, language } = useTranslation();
    const [data, setData] = useState<RealTimeRiskAnalysis | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const result = await parametricApi.getPortfolioRisk();
                setData(result);
            } catch (error) {
                console.error("Error fetching risk analysis:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return <Skeleton className="h-[400px] w-full" />;
    }

    const formatCurrency = (val: number) => {
        return `${t('common.currency')} ${val.toLocaleString(language, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const getRiskLabel = (level: string) => {
        switch (level.toLowerCase()) {
            case 'high': return t('audit.risk.high');
            case 'medium': return t('audit.risk.medium');
            case 'low': return t('audit.risk.low');
            case 'critical': return t('audit.risk.critical');
            default: return level;
        }
    };

    const getRiskColor = (level: string) => {
        switch (level.toLowerCase()) {
            case 'high': return 'text-red-600 bg-red-50 border-red-200';
            case 'medium': return 'text-amber-600 bg-amber-50 border-amber-200';
            case 'low': return 'text-emerald-600 bg-emerald-50 border-emerald-200';
            default: return 'text-slate-600 bg-slate-50 border-slate-200';
        }
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border-red-100 bg-red-50/20">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <ShieldAlert className="h-4 w-4 text-red-600" />
                            {t('risk.monitor.exposure')}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-700">
                            {formatCurrency(data?.summary?.total_exposure || 0)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            {t('risk.monitor.exposureDesc')}
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-amber-100 bg-amber-50/20">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-amber-600" />
                            {t('risk.monitor.payout')}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-amber-700">
                            {formatCurrency(data?.summary?.potential_payout || 0)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            {t('risk.monitor.policiesAffected', { count: data?.summary?.impacted_policies_count || 0 })}
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-blue-100 bg-blue-50/20">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <Info className="h-4 w-4 text-blue-600" />
                            {t('risk.monitor.activeAlerts')}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-700">
                            {data?.summary?.total_alerts || 0}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            {t('risk.monitor.alertsDesc')}
                        </p>
                    </CardContent>
                </Card>
            </div>

            {data?.impacted_policies && data.impacted_policies.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg font-semibold flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            {t('risk.monitor.title')}
                        </CardTitle>
                        <CardDescription>
                            {t('risk.monitor.description')}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-md border overflow-hidden">
                            <Table>
                                <TableHeader className="bg-muted/50">
                                    <TableRow>
                                        <TableHead>{t('risk.monitor.table.policy')}</TableHead>
                                        <TableHead>{t('risk.monitor.table.location')}</TableHead>
                                        <TableHead>{t('risk.monitor.table.event')}</TableHead>
                                        <TableHead>{t('risk.monitor.table.severity')}</TableHead>
                                        <TableHead className="text-right">{t('risk.monitor.table.potentialPayout')}</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {data.impacted_policies.map((policy) => (
                                        <TableRow key={policy.policy_id}>
                                            <TableCell className="font-medium">{policy.policy_number}</TableCell>
                                            <TableCell className="flex items-center gap-1">
                                                <MapPin className="h-3 w-3 text-muted-foreground" />
                                                {policy.location}
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className="capitalize">
                                                    {policy.disaster_type}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge className={getRiskColor(policy.severity)}>
                                                    {getRiskLabel(policy.severity)}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-right font-semibold text-red-600">
                                                {formatCurrency(policy.potential_payout)}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>
            )}

            {(!data?.impacted_policies || data.impacted_policies.length === 0) && (
                <Alert className="border-emerald-200 bg-emerald-50/50">
                    <AlertTriangle className="h-4 w-4 text-emerald-600" />
                    <AlertTitle className="text-emerald-800">{t('risk.monitor.stable.title')}</AlertTitle>
                    <AlertDescription className="text-emerald-700/80">
                        {t('risk.monitor.stable.desc')}
                    </AlertDescription>
                </Alert>
            )}
        </div>
    );
}
