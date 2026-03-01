import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import {
    Shield,
    AlertTriangle,
    FileText,
    Download,
    Filter,
    Activity,
    CheckCircle,
    XCircle,
    Clock,
    TrendingUp,
    BarChart3,
    PieChart
} from "lucide-react";
import { auditApi, AuditLogEntry, ComplianceReport } from '@/lib/api';
import { useTranslation } from "@/hooks/useTranslation";

interface AuditDashboardProps {
    className?: string;
}

export const AuditDashboard: React.FC<AuditDashboardProps> = ({ className }) => {
    const { t, language } = useTranslation();
    const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
    const [complianceReport, setComplianceReport] = useState<ComplianceReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        operation: '',
        status: '',
        user_id: '',
        start_date: '',
        end_date: '',
        limit: 50
    });
    const [activeTab, setActiveTab] = useState('logs');

    const loadAuditData = useCallback(async () => {
        try {
            setLoading(true);
            const [logsData, reportData] = await Promise.all([
                auditApi.getAuditLogs(filters),
                auditApi.getComplianceReport()
            ]);
            setAuditLogs(logsData);
            setComplianceReport(reportData);
        } catch (error) {
            console.error('Erro ao carregar dados de auditoria:', error);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    useEffect(() => {
        loadAuditData();
    }, [loadAuditData]);

    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'success':
                return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />{t('audit.status.success')}</Badge>;
            case 'error':
                return <Badge variant="danger"><XCircle className="w-3 h-3 mr-1" />{t('audit.status.error')}</Badge>;
            case 'warning':
                return <Badge variant="secondary" className="bg-yellow-500"><AlertTriangle className="w-3 h-3 mr-1" />{t('audit.status.warning')}</Badge>;
            default:
                return <Badge variant="outline"><Clock className="w-3 h-3 mr-1" />{t('audit.status.pending')}</Badge>;
        }
    };

    const getOperationIcon = (operation: string) => {
        switch (operation) {
            case 'pricing_calculation':
                return <BarChart3 className="w-4 h-4" />;
            case 'ml_prediction':
                return <TrendingUp className="w-4 h-4" />;
            case 'microsegmentation_analysis':
                return <PieChart className="w-4 h-4" />;
            case 'external_data_retrieval':
                return <Activity className="w-4 h-4" />;
            default:
                return <FileText className="w-4 h-4" />;
        }
    };

    const getOperationLabel = (operation: string) => {
        switch (operation) {
            case 'pricing_calculation': return t('audit.filters.pricing');
            case 'ml_prediction': return t('audit.filters.ml');
            case 'microsegmentation_analysis': return t('audit.filters.microsegmentation');
            case 'external_data_retrieval': return t('audit.filters.externalData');
            default: return operation.replace('_', ' ');
        }
    };

    const exportReport = async (format: 'pdf' | 'excel') => {
        try {
            // Implementar exportação
            console.log(`Exportando relatório em formato ${format}`);
        } catch (error) {
            console.error('Erro ao exportar relatório:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className={`space-y-6 ${className}`}>
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                        <Shield className="h-6 w-6" />
                        {t('audit.title')}
                    </h2>
                    <p className="text-muted-foreground">
                        {t('audit.description')}
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => exportReport('pdf')}>
                        <Download className="w-4 h-4 mr-2" />
                        {t('audit.export.pdf')}
                    </Button>
                    <Button variant="outline" onClick={() => exportReport('excel')}>
                        <Download className="w-4 h-4 mr-2" />
                        {t('audit.export.excel')}
                    </Button>
                </div>
            </div>

            {/* Compliance Overview */}
            {complianceReport && (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">{t('audit.stats.totalOperations')}</CardTitle>
                            <Activity className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{complianceReport.summary.total_operations}</div>
                            <p className="text-xs text-muted-foreground">
                                {t('audit.stats.last30Days')}
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">{t('audit.stats.successful')}</CardTitle>
                            <CheckCircle className="h-4 w-4 text-green-600" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-green-600">
                                {complianceReport.summary.successful_operations}
                            </div>
                            <Progress
                                value={(complianceReport.summary.successful_operations / complianceReport.summary.total_operations) * 100}
                                className="mt-2"
                            />
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">{t('audit.stats.violations')}</CardTitle>
                            <AlertTriangle className="h-4 w-4 text-red-600" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-red-600">
                                {complianceReport.summary.compliance_violations}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                {t('audit.stats.attentionRequired')}
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">{t('audit.stats.riskDistribution')}</CardTitle>
                            <Shield className="h-4 w-4 text-blue-600" />
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span>{t('audit.risk.low')}</span>
                                    <span>{complianceReport.risk_distribution.low}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span>{t('audit.risk.medium')}</span>
                                    <span>{complianceReport.risk_distribution.medium}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span>{t('audit.risk.high')}</span>
                                    <span>{complianceReport.risk_distribution.high}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span>{t('audit.risk.critical')}</span>
                                    <span>{complianceReport.risk_distribution.critical}%</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Critical Alerts */}
            {complianceReport && complianceReport.violations.length > 0 && (
                <Alert className="border-red-200 bg-red-50">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <AlertTitle className="text-red-800">{t('audit.violations.detected')}</AlertTitle>
                    <AlertDescription className="text-red-700">
                        {t('audit.violations.count', { count: complianceReport.violations.length })}
                        <Button variant="link" className="p-0 h-auto text-red-700 underline ml-2">
                            {t('audit.violations.viewDetails')}
                        </Button>
                    </AlertDescription>
                </Alert>
            )}

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList>
                    <TabsTrigger value="logs">{t('audit.tabs.logs')}</TabsTrigger>
                    <TabsTrigger value="violations">{t('audit.tabs.violations')}</TabsTrigger>
                    <TabsTrigger value="analytics">{t('audit.tabs.analytics')}</TabsTrigger>
                </TabsList>

                <TabsContent value="logs" className="space-y-4">
                    {/* Filters */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Filter className="h-4 w-4" />
                                {t('audit.filters.title')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                <div className="space-y-2">
                                    <Label htmlFor="operation">{t('audit.filters.operation')}</Label>
                                    <Select value={filters.operation} onValueChange={(value) => handleFilterChange('operation', value)}>
                                        <SelectTrigger>
                                            <SelectValue placeholder={t('audit.filters.allOperations')} />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="">{t('audit.filters.all')}</SelectItem>
                                            <SelectItem value="pricing_calculation">{t('audit.filters.pricing')}</SelectItem>
                                            <SelectItem value="ml_prediction">{t('audit.filters.ml')}</SelectItem>
                                            <SelectItem value="microsegmentation_analysis">{t('audit.filters.microsegmentation')}</SelectItem>
                                            <SelectItem value="external_data_retrieval">{t('audit.filters.externalData')}</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="status">{t('audit.filters.status')}</Label>
                                    <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
                                        <SelectTrigger>
                                            <SelectValue placeholder={t('audit.filters.allStatus')} />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="">{t('audit.filters.all')}</SelectItem>
                                            <SelectItem value="success">{t('audit.status.success')}</SelectItem>
                                            <SelectItem value="error">{t('audit.status.error')}</SelectItem>
                                            <SelectItem value="warning">{t('audit.status.warning')}</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="user_id">{t('audit.filters.userId')}</Label>
                                    <Input
                                        id="user_id"
                                        placeholder={t('audit.filters.userIdPlaceholder')}
                                        value={filters.user_id}
                                        onChange={(e) => handleFilterChange('user_id', e.target.value)}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="start_date">{t('audit.filters.startDate')}</Label>
                                    <Input
                                        id="start_date"
                                        type="date"
                                        value={filters.start_date}
                                        onChange={(e) => handleFilterChange('start_date', e.target.value)}
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Audit Logs Table */}
                    <Card>
                        <CardHeader>
                            <CardTitle>{t('audit.tabs.logs')}</CardTitle>
                            <CardDescription>
                                {t('audit.description')}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>{t('audit.table.timestamp')}</TableHead>
                                        <TableHead>{t('audit.table.operation')}</TableHead>
                                        <TableHead>{t('audit.table.status')}</TableHead>
                                        <TableHead>{t('audit.table.user')}</TableHead>
                                        <TableHead>{t('audit.table.resource')}</TableHead>
                                        <TableHead>{t('audit.table.details')}</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {auditLogs.map((log) => (
                                        <TableRow key={log.id}>
                                            <TableCell>
                                                {new Date(log.timestamp).toLocaleString(language)}
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    {getOperationIcon(log.operation)}
                                                    <span>
                                                        {getOperationLabel(log.operation)}
                                                    </span>
                                                </div>
                                            </TableCell>
                                            <TableCell>{getStatusBadge(log.status)}</TableCell>
                                            <TableCell>{log.user_id || 'System'}</TableCell>
                                            <TableCell>{log.resource_id || '-'}</TableCell>
                                            <TableCell>
                                                <Button variant="ghost" size="sm">
                                                    <FileText className="w-4 h-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="violations" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>{t('audit.tabs.violations')}</CardTitle>
                            <CardDescription>
                                {t('audit.stats.attentionRequired')}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {complianceReport && complianceReport.violations.length > 0 ? (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>{t('audit.table.timestamp')}</TableHead>
                                            <TableHead>{t('audit.table.operation')}</TableHead>
                                            <TableHead>Tipo</TableHead>
                                            <TableHead>Severidade</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead>{t('audit.table.details')}</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {complianceReport.violations.map((violation) => (
                                            <TableRow key={violation.id}>
                                                <TableCell>
                                                    {new Date(violation.timestamp).toLocaleString(language)}
                                                </TableCell>
                                                <TableCell>{getOperationLabel(violation.operation)}</TableCell>
                                                <TableCell>{violation.violation_type}</TableCell>
                                                <TableCell>
                                                    <Badge variant={
                                                        violation.severity === 'critical' ? 'danger' :
                                                            violation.severity === 'high' ? 'warning' :
                                                                'outline'
                                                    }>
                                                        {violation.severity}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>{violation.resolution_status}</TableCell>
                                                <TableCell>
                                                    <Button variant="outline" size="sm">
                                                        {t('audit.violations.resolve')}
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            ) : (
                                <div className="text-center py-8">
                                    <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                                    <h3 className="text-lg font-medium text-green-800">{t('audit.violations.none')}</h3>
                                    <p className="text-muted-foreground">
                                        {t('audit.violations.noneDesc')}
                                    </p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="analytics" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>{t('audit.analytics.operationType')}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                                        <BarChart3 className="h-8 w-8 text-muted-foreground" />
                                        <span className="ml-2 text-muted-foreground">{t('audit.analytics.distributionChart')}</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>{t('audit.analytics.riskTrends')}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                                        <TrendingUp className="h-8 w-8 text-muted-foreground" />
                                        <span className="ml-2 text-muted-foreground">{t('audit.analytics.trendsChart')}</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
};