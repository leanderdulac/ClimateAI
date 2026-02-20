import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Loader2, AlertTriangle, CheckCircle2, TrendingUp, DollarSign } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface SimulationResult {
    contract_summary: string;
    metrics: {
        AAL: number;
        p_positive: number;
        years_used: number;
    };
    risk_metrics: {
        VaR_95: number;
        TVaR_95: number;
        VaR_99: number;
        TVaR_99: number;
    };
    pricing: {
        technical_rate: number;
        commercial_rate: number;
        commercial_premium: number;
        breakdown: any;
    };
    ep_curve: {
        prob_exceedance: number[];
        loss: number[];
    };
    payouts_history: any[];
}

export function ParametricSimulator() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<SimulationResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [params, setParams] = useState({
        latitude: -23.55,
        longitude: -46.63,
        trigger_mm: 100,
        exhaustion_mm: 200,
        max_payout: 1000000,
        index_type: 'max_3day'
    });

    const handleSimulate = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/parametric/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    latitude: params.latitude,
                    longitude: params.longitude,
                    contract: {
                        area_id: "custom_sim",
                        start_date: "01-01",
                        end_date: "03-31",
                        trigger_mm: params.trigger_mm,
                        exhaustion_mm: params.exhaustion_mm,
                        max_payout: params.max_payout,
                        index_type: params.index_type
                    },
                    years_back: 20,
                    include_ep_curve: true
                })
            });

            if (!response.ok) {
                throw new Error(`Simulation failed: ${response.statusText}`);
            }

            const data = await response.json();
            setResult(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
    };

    const formatPercent = (val: number) => {
        return new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 2 }).format(val);
    };

    // Prepare EP Curve Data for Chart
    const epCurveData = result?.ep_curve?.prob_exceedance?.map((prob, i) => ({
        prob,
        loss: result.ep_curve?.loss[i]
    })).reverse() || [];

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Simulador de Contrato Paramétrico (Chuva)
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                        <div className="space-y-2">
                            <Label>Latitude</Label>
                            <Input
                                type="number"
                                value={params.latitude}
                                onChange={e => setParams({ ...params, latitude: parseFloat(e.target.value) })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Longitude</Label>
                            <Input
                                type="number"
                                value={params.longitude}
                                onChange={e => setParams({ ...params, longitude: parseFloat(e.target.value) })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Tipo de Índice</Label>
                            <Select
                                value={params.index_type}
                                onValueChange={v => setParams({ ...params, index_type: v })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="max_3day">Máxima Chuva 3 Dias</SelectItem>
                                    <SelectItem value="cum_period">Chuva Acumulada</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Gatilho (mm)</Label>
                            <Input
                                type="number"
                                value={params.trigger_mm}
                                onChange={e => setParams({ ...params, trigger_mm: parseFloat(e.target.value) })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Exaustão (mm)</Label>
                            <Input
                                type="number"
                                value={params.exhaustion_mm}
                                onChange={e => setParams({ ...params, exhaustion_mm: parseFloat(e.target.value) })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Soma Segurada (R$)</Label>
                            <Input
                                type="number"
                                value={params.max_payout}
                                onChange={e => setParams({ ...params, max_payout: parseFloat(e.target.value) })}
                            />
                        </div>
                    </div>

                    <Button
                        onClick={handleSimulate}
                        disabled={loading}
                        className="w-full md:w-auto"
                    >
                        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                        Rodar Simulação Atuarial
                    </Button>

                    {error && (
                        <Alert variant="destructive" className="mt-4">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>Erro</AlertTitle>
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}
                </CardContent>
            </Card>

            {result && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Pricing Card */}
                    <Card className="bg-slate-50 border-emerald-200">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-emerald-800">
                                <DollarSign className="h-5 w-5" />
                                Precificação Sugerida
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex justify-between items-center text-lg font-semibold">
                                <span>Prêmio Comercial:</span>
                                <span className="text-emerald-700">{formatCurrency(result.pricing.commercial_premium)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm text-slate-600">
                                <span>Taxa Comercial:</span>
                                <span>{formatPercent(result.pricing.commercial_rate)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm text-slate-600">
                                <span>Taxa Técnica (Pura + Carga):</span>
                                <span>{formatPercent(result.pricing.technical_rate)}</span>
                            </div>
                            <div className="pt-4 border-t border-slate-200">
                                <h4 className="font-semibold mb-2 text-sm text-slate-700">Métricas de Risco de Cauda</h4>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <span className="block text-slate-500">VaR 99%</span>
                                        <span className="font-medium">{formatCurrency(result.risk_metrics.VaR_99)}</span>
                                    </div>
                                    <div>
                                        <span className="block text-slate-500">TVaR 99%</span>
                                        <span className="font-medium">{formatCurrency(result.risk_metrics.TVaR_99)}</span>
                                    </div>
                                    <div>
                                        <span className="block text-slate-500">Perda Média (AAL)</span>
                                        <span className="font-medium">{formatCurrency(result.metrics.AAL)}</span>
                                    </div>
                                    <div>
                                        <span className="block text-slate-500">Prob. Pagamento</span>
                                        <span className="font-medium">{formatPercent(result.metrics.p_positive)}</span>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Historical Payouts Chart */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Histórico de Pagamentos (Backtesting)</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={result.payouts_history}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="year" />
                                    <YAxis tickFormatter={(val) => `R$${val / 1000}k`} />
                                    <Tooltip formatter={(value: number) => formatCurrency(value)} />
                                    <Legend />
                                    <Bar dataKey="payout" name="Indenização" fill="#059669" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>

                    {/* EP Curve Chart */}
                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <CardTitle>Curva de Excedência de Perda (EP Curve)</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[350px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={epCurveData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis
                                        dataKey="prob"
                                        label={{ value: 'Probabilidade de Excedência (%)', position: 'insideBottom', offset: -5 }}
                                        domain={[0, 100]}
                                        type="number"
                                    />
                                    <YAxis
                                        tickFormatter={(val) => `R$${val / 1000}k`}
                                        label={{ value: 'Perda (R$)', angle: -90, position: 'insideLeft' }}
                                    />
                                    <Tooltip
                                        formatter={(value: number) => formatCurrency(value)}
                                        labelFormatter={(label) => `Prob. Excedência: ${label}%`}
                                    />
                                    <Legend />
                                    <Line type="monotone" dataKey="loss" name="Perda Estimada" stroke="#2563eb" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                            <p className="text-xs text-slate-500 mt-2 text-center">
                                *O eixo X mostra a probabilidade de uma perda exceder o valor no eixo Y.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
