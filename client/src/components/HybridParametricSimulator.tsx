import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { Loader2, AlertTriangle, TrendingUp, CloudRain, DollarSign, Activity } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { parametricApi, HybridSimulationResponse } from "@/lib/parametricApi";

export function HybridParametricSimulator() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<HybridSimulationResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [params, setParams] = useState({
        municipio: 'SANTOS',
        uf: 'SP',
        dataInicio: '2025-01-01',
        dataFim: '2025-01-10',
        insuredCapital: 100000
    });

    const todayStr = new Date().toISOString().split('T')[0];

    const handleSimulate = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await parametricApi.simulateHybridIndex(
                params.municipio,
                params.uf,
                params.dataInicio,
                params.dataFim,
                params.insuredCapital
            );
            if (data.error) throw new Error(data.error);
            setResult(data);
        } catch (err: any) {
            setError(err.message || "Erro desconhecido ao simular");
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
    };

    const formatPercent = (val: number) => {
        return new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 1 }).format(val);
    };

    // Payout Tiers definidos no backend (ex: Moderado > 50mm, Severo > 100mm, Extremo > 150mm)
    const tiers = [
        { name: "Moderado (30%)", mm: 50, color: "#eab308" },
        { name: "Severo (60%)", mm: 100, color: "#f97316" },
        { name: "Extremo (100%)", mm: 150, color: "#ef4444" }
    ];

    // Formata o histórico de chuvas diárias
    const chartData = result?.recent_data_sample?.map(day => ({
        ...day,
        displayDate: day.data.substring(5) // MM-DD
    })) || [];

    return (
        <div className="space-y-6">
            <Card className="bg-white shadow-sm border-slate-200/60 backdrop-blur-sm">
                <CardHeader className="bg-gradient-to-r from-emerald-50 to-teal-50/50 border-b border-slate-100">
                    <CardTitle className="flex items-center gap-2 text-emerald-800">
                        <CloudRain className="h-5 w-5 text-emerald-600" />
                        Simulador Paramétrico Híbrido (Chuvas)
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                        <div className="space-y-2">
                            <Label>Município</Label>
                            <Input
                                value={params.municipio}
                                onChange={e => setParams({ ...params, municipio: e.target.value })}
                                placeholder="ex: SAO PAULO"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>UF</Label>
                            <Input
                                value={params.uf}
                                onChange={e => setParams({ ...params, uf: e.target.value.toUpperCase() })}
                                maxLength={2}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Data Início</Label>
                            <Input
                                type="date"
                                value={params.dataInicio}
                                max={todayStr}
                                onChange={e => setParams({ ...params, dataInicio: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Data Fim</Label>
                            <Input
                                type="date"
                                value={params.dataFim}
                                max={todayStr}
                                onChange={e => setParams({ ...params, dataFim: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Capital Segurado (R$)</Label>
                            <Input
                                type="number"
                                value={params.insuredCapital}
                                onChange={e => setParams({ ...params, insuredCapital: parseFloat(e.target.value) })}
                            />
                        </div>
                    </div>

                    <Button
                        onClick={handleSimulate}
                        disabled={loading || !params.municipio || !params.uf}
                        className="w-full md:w-auto bg-emerald-600 hover:bg-emerald-700 text-white"
                    >
                        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Activity className="mr-2 h-4 w-4" />}
                        Executar Simulação
                    </Button>

                    {error && (
                        <Alert variant="destructive" className="mt-4">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>Erro na Simulação</AlertTitle>
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}
                </CardContent>
            </Card>

            {result && result.report && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4">

                    {/* Metrics Cards */}
                    <div className="lg:col-span-1 space-y-4">
                        <Card className="bg-emerald-50/50 border-emerald-100">
                            <CardContent className="pt-6">
                                <div className="flex justify-between items-start">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-emerald-600">Payout Estimado</p>
                                        <p className="text-3xl font-bold text-emerald-900">
                                            {formatCurrency(result.report.payout_total_estimado)}
                                        </p>
                                    </div>
                                    <div className="p-2 bg-emerald-100 rounded-full">
                                        <DollarSign className="h-5 w-5 text-emerald-600" />
                                    </div>
                                </div>
                                <div className="mt-4 text-sm text-emerald-700">
                                    Disparou em {result.report.eventos_gatilho} dias analisados ({formatPercent(result.report.taxa_disparo)})
                                </div>
                            </CardContent>
                        </Card>

                        <div className="grid grid-cols-2 gap-4">
                            <Card className="bg-slate-50 border-slate-200">
                                <CardContent className="pt-6">
                                    <p className="text-sm font-medium text-slate-500">Chuva Máxima</p>
                                    <p className="text-xl font-bold text-slate-800">{result.report.chuva_maxima.toFixed(1)} mm</p>
                                </CardContent>
                            </Card>
                            <Card className="bg-slate-50 border-slate-200">
                                <CardContent className="pt-6">
                                    <p className="text-sm font-medium text-slate-500">Volume Total</p>
                                    <p className="text-xl font-bold text-slate-800">
                                        {(result.report.chuva_media * result.report.total_registros).toFixed(1)} mm
                                    </p>
                                </CardContent>
                            </Card>
                        </div>

                        <Card className="bg-slate-50 border-slate-200">
                            <CardContent className="pt-6">
                                <p className="text-sm font-medium text-slate-500 mb-2">Fonte de Dados Utilizada</p>
                                <div className="flex flex-wrap gap-2">
                                    {result.report.fontes_utilizadas.map(fonte => (
                                        <span key={fonte} className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 text-xs font-medium">
                                            {fonte}
                                        </span>
                                    ))}
                                </div>
                                <p className="text-xs text-slate-400 mt-3">
                                    Resolvido automaticamente via indexador inteligente.
                                </p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Chart Area */}
                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <CardTitle className="text-lg">Precipitação Diária vs Gatilhos Paramétricos</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[350px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis dataKey="displayDate" />
                                    <YAxis tickFormatter={(val) => `${val}mm`} />
                                    <Tooltip
                                        cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                                        content={({ active, payload }) => {
                                            if (active && payload && payload.length) {
                                                const data = payload[0].payload;
                                                return (
                                                    <div className="bg-white p-3 border rounded shadow-lg max-w-xs">
                                                        <p className="font-bold border-b pb-1 mb-2">{data.data}</p>
                                                        <p className="text-sm text-blue-600">Chuva: {data.acumulado_mm.toFixed(1)} mm</p>
                                                        <p className="text-sm text-slate-600">Fonte: {data.fonte}</p>
                                                        {data.triggered && (
                                                            <div className="mt-2 pt-2 border-t">
                                                                <p className="text-sm font-bold text-emerald-600">Gatilho: {data.tier_name}</p>
                                                                <p className="text-sm text-emerald-700">Payout: {formatCurrency(data.payout_value)}</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            }
                                            return null;
                                        }}
                                    />
                                    <Legend />

                                    {/* Gatilhos / Tiers */}
                                    {tiers.map((tier) => (
                                        <ReferenceLine
                                            key={tier.name}
                                            y={tier.mm}
                                            stroke={tier.color}
                                            strokeDasharray="3 3"
                                            label={{ position: 'top', value: tier.name, fill: tier.color, fontSize: 12 }}
                                        />
                                    ))}

                                    <Bar dataKey="acumulado_mm" name="Precipitação (mm)" radius={[4, 4, 0, 0]}>
                                        {chartData.map((entry, index) => (
                                            <Cell
                                                key={`cell-${index}`}
                                                fill={entry.triggered ? "#10b981" : "#3b82f6"}
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
