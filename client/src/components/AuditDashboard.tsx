import React, { useState, useEffect } from 'react';
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

interface AuditDashboardProps {
    className?: string;
}

export const AuditDashboard: React.FC<AuditDashboardProps> = ({ className }) => {
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

    useEffect(() => {
        loadAuditData();
    }, [filters]);

    const loadAuditData = async () => {
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
    };

    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'success':
                return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Sucesso</Badge>;
            case 'error':
                return <Badge variant="danger"><XCircle className="w-3 h-3 mr-1" />Erro</Badge>;
            case 'warning':
                return <Badge variant="secondary" className="bg-yellow-500"><AlertTriangle className="w-3 h-3 mr-1" />Aviso</Badge>;
            default:
                return <Badge variant="outline"><Clock className="w-3 h-3 mr-1" />Pendente</Badge>;
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
                        Dashboard de Auditoria e Compliance
                    </h2>
                    <p className="text-muted-foreground">
                        Monitoramento completo de operações e conformidade regulatória
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => exportReport('pdf')}>
                        <Download className="w-4 h-4 mr-2" />
                        Exportar PDF
                    </Button>
                    <Button variant="outline" onClick={() => exportReport('excel')}>
                        <Download className="w-4 h-4 mr-2" />
                        Exportar Excel
                    </Button>
                </div>
            </div>

            {/* Compliance Overview */}
            {complianceReport && (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total de Operações</CardTitle>
                            <Activity className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{complianceReport.summary.total_operations}</div>
                            <p className="text-xs text-muted-foreground">
                                Últimos 30 dias
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Operações Bem-sucedidas</CardTitle>
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
                            <CardTitle className="text-sm font-medium">Violações de Compliance</CardTitle>
                            <AlertTriangle className="h-4 w-4 text-red-600" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-red-600">
                                {complianceReport.summary.compliance_violations}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Requer atenção imediata
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Distribuição de Risco</CardTitle>
                            <Shield className="h-4 w-4 text-blue-600" />
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span>Baixo</span>
                                    <span>{complianceReport.risk_distribution.low}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span>Médio</span>
                                    <span>{complianceReport.risk_distribution.medium}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span>Alto</span>
                                    <span>{complianceReport.risk_distribution.high}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span>Crítico</span>
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
                    <AlertTitle className="text-red-800">Violações Críticas Detectadas</AlertTitle>
                    <AlertDescription className="text-red-700">
                        {complianceReport.violations.length} violações de compliance requerem atenção imediata.
                        <Button variant="link" className="p-0 h-auto text-red-700 underline">
                            Ver detalhes
                        </Button>
                    </AlertDescription>
                </Alert>
            )}

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList>
                    <TabsTrigger value="logs">Logs de Auditoria</TabsTrigger>
                    <TabsTrigger value="violations">Violações de Compliance</TabsTrigger>
                    <TabsTrigger value="analytics">Análises</TabsTrigger>
                </TabsList>

                <TabsContent value="logs" className="space-y-4">
                    {/* Filters */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Filter className="h-4 w-4" />
                                Filtros
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                <div className="space-y-2">
                                    <Label htmlFor="operation">Operação</Label>
                                    <Select value={filters.operation} onValueChange={(value) => handleFilterChange('operation', value)}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Todas as operações" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="">Todas</SelectItem>
                                            <SelectItem value="pricing_calculation">Cálculo de Preço</SelectItem>
                                            <SelectItem value="ml_prediction">Predição ML</SelectItem>
                                            <SelectItem value="microsegmentation_analysis">Análise de Microsegmentação</SelectItem>
                                            <SelectItem value="external_data_retrieval">Recuperação de Dados Externos</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="status">Status</Label>
                                    <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Todos os status" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="">Todos</SelectItem>
                                            <SelectItem value="success">Sucesso</SelectItem>
                                            <SelectItem value="error">Erro</SelectItem>
                                            <SelectItem value="warning">Aviso</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="user_id">ID do Usuário</Label>
                                    <Input
                                        id="user_id"
                                        placeholder="Digite o ID do usuário"
                                        value={filters.user_id}
                                        onChange={(e) => handleFilterChange('user_id', e.target.value)}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="start_date">Data Inicial</Label>
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
                            <CardTitle>Logs de Auditoria</CardTitle>
                            <CardDescription>
                                Histórico detalhado de todas as operações do sistema
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Data/Hora</TableHead>
                                        <TableHead>Operação</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Usuário</TableHead>
                                        <TableHead>Recurso</TableHead>
                                        <TableHead>Detalhes</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {auditLogs.map((log) => (
                                        <TableRow key={log.id}>
                                            <TableCell>
                                                {new Date(log.timestamp).toLocaleString('pt-BR')}
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    {getOperationIcon(log.operation)}
                                                    <span className="capitalize">
                                                        {log.operation.replace('_', ' ')}
                                                    </span>
                                                </div>
                                            </TableCell>
                                            <TableCell>{getStatusBadge(log.status)}</TableCell>
                                            <TableCell>{log.user_id || 'Sistema'}</TableCell>
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
                            <CardTitle>Violações de Compliance</CardTitle>
                            <CardDescription>
                                Lista de violações detectadas que requerem atenção
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {complianceReport && complianceReport.violations.length > 0 ? (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Data/Hora</TableHead>
                                            <TableHead>Operação</TableHead>
                                            <TableHead>Tipo de Violação</TableHead>
                                            <TableHead>Severidade</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead>Ações</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {complianceReport.violations.map((violation) => (
                                            <TableRow key={violation.id}>
                                                <TableCell>
                                                    {new Date(violation.timestamp).toLocaleString('pt-BR')}
                                                </TableCell>
                                                <TableCell>{violation.operation}</TableCell>
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
                                                        Resolver
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            ) : (
                                <div className="text-center py-8">
                                    <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                                    <h3 className="text-lg font-medium text-green-800">Nenhuma Violação Detectada</h3>
                                    <p className="text-muted-foreground">
                                        Todas as operações estão em conformidade com as regras estabelecidas.
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
                                <CardTitle>Distribuição por Tipo de Operação</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {/* Placeholder para gráfico de distribuição */}
                                    <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                                        <BarChart3 className="h-8 w-8 text-muted-foreground" />
                                        <span className="ml-2 text-muted-foreground">Gráfico de distribuição</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Tendências de Risco</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {/* Placeholder para gráfico de tendências */}
                                    <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                                        <TrendingUp className="h-8 w-8 text-muted-foreground" />
                                        <span className="ml-2 text-muted-foreground">Gráfico de tendências</span>
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