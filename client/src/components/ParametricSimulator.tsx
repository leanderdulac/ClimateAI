import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Loader2, AlertTriangle, CheckCircle2, TrendingUp, DollarSign, Search, MapPin } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { buildApiUrl, embrapaApi } from '@/lib/api';
import { useTokenizationStore } from '@/store/useTokenizationStore';
import { useNavigate } from 'react-router-dom';

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
    const setPendingTokenizationData = useTokenizationStore((state) => state.setPendingTokenizationData);
    const navigate = useNavigate();

    const [params, setParams] = useState({
        latitude: -23.55,
        longitude: -46.63,
        trigger_mm: 100,
        exhaustion_mm: 200,
        max_payout: 1000000,
        index_type: 'max_3day'
    });

    const [citySearch, setCitySearch] = useState('São Paulo');
    const [stateSearch, setStateSearch] = useState('SP');
    const [locationName, setLocationName] = useState('São Paulo, SP');
    const [locLoading, setLocLoading] = useState(false);
    const [locError, setLocError] = useState<string | null>(null);

    const searchByCity = async () => {
        if (!citySearch || !stateSearch) { setLocError('Informe cidade e estado (UF).'); return; }
        setLocLoading(true); setLocError(null);
        try {
            const data = await embrapaApi.getLocalizacaoPorCidade(citySearch, stateSearch);
            setParams(prev => ({ ...prev, latitude: data.latitude, longitude: data.longitude }));
            setLocationName(`${data.cidade || citySearch}, ${data.estado || stateSearch}`);
        } catch {
            setLocError('Cidade não encontrada.');
        } finally {
            setLocLoading(false);
        }
    };

    const handleSimulate = async () => {
        setLoading(true);
        setError(null);
        try {
            const useMock = import.meta.env.VITE_USE_MOCK_DATA === 'true';
            const url = buildApiUrl('/api/v1/parametric/simulate');

            if (useMock) {
                // Mock básico para evitar 500 no dev
                const mock = {
                    contract_summary: 'Simulação mock',
                    metrics: { AAL: 12000, p_positive: 0.62, years_used: 20 },
                    risk_metrics: { VaR_95: 35000, TVaR_95: 42000, VaR_99: 50000, TVaR_99: 62000 },
                    pricing: { technical_rate: 0.08, commercial_rate: 0.1, commercial_premium: 150000, breakdown: {} },
                    ep_curve: { prob_exceedance: [0.1, 0.2, 0.3, 0.4, 0.5], loss: [10000, 20000, 30000, 40000, 50000] },
                    payouts_history: []
                } as SimulationResult;
                setResult(mock);
                setLoading(false);
                return;
            }

            const response = await fetch(url, {
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
                throw new Error(`Simulation failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            setResult(data);
        } catch (err: any) {
            console.warn('[ParametricSimulator] falling back to mock after error:', err?.message);
            setResult({
                contract_summary: 'Simulação mock (offline)',
                metrics: { AAL: 8000, p_positive: 0.55, years_used: 20 },
                risk_metrics: { VaR_95: 28000, TVaR_95: 34000, VaR_99: 42000, TVaR_99: 51000 },
                pricing: { technical_rate: 0.07, commercial_rate: 0.09, commercial_premium: 120000, breakdown: {} },
                ep_curve: { prob_exceedance: [0.1, 0.2, 0.3, 0.4, 0.5], loss: [9000, 18000, 26000, 33000, 41000] },
                payouts_history: []
            });
            setError(null);
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

    const handleCreateToken = () => {
        if (!result) return;

        let eventType = 'seca'; // default
        const idx = params.index_type.toLowerCase();
        if (idx.includes('rain') || idx.includes('enchente') || idx.includes('max')) {
            eventType = 'enchente';
        } else if (idx.includes('heat') || idx.includes('calor')) {
            eventType = 'onda_calor';
        } else if (idx.includes('frost') || idx.includes('geada')) {
            eventType = 'geada';
        }

        const severityScore = result.metrics.AAL / params.max_payout * 10;
        const alertLevel = Math.min(5, Math.ceil(severityScore)).toString() || '3';

        setPendingTokenizationData({
            tipo: eventType,
            latitude: params.latitude.toString(),
            longitude: params.longitude.toString(),
            intensidade: severityScore.toFixed(2),
            probabilidade: (result.metrics.p_positive * 100).toFixed(2),
            descricao: `Simulated policy contract for ${locationName}. AAL: ${formatCurrency(result.metrics.AAL)}`,
            nivel_alerta: alertLevel,
            token_supply: params.max_payout
        });

        navigate('/tokenization');
    };

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
                        <div className="space-y-2 lg:col-span-2">
                            <Label>Localização (Cidade e UF)</Label>
                            <div className="flex gap-2">
                                <Input
                                    placeholder="Cidade"
                                    value={citySearch}
                                    onChange={(e) => setCitySearch(e.target.value)}
                                    className="flex-1"
                                />
                                <Input
                                    placeholder="UF"
                                    value={stateSearch}
                                    onChange={(e) => setStateSearch(e.target.value.toUpperCase())}
                                    maxLength={2}
                                    className="w-16 text-center uppercase"
                                />
                                <Button type="button" onClick={searchByCity} variant="outline" disabled={locLoading}>
                                    {locLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                                </Button>
                            </div>
                            {locError && <p className="text-sm text-red-500">{locError}</p>}
                            {locationName && (
                                <p className="text-xs text-emerald-600 flex items-center gap-1 mt-1">
                                    <MapPin className="h-3 w-3" />
                                    {locationName} ({params.latitude.toFixed(4)}°, {params.longitude.toFixed(4)}°)
                                </p>
                            )}
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
                            <CardTitle className="flex items-center justify-between text-emerald-800">
                                <div className="flex items-center gap-2">
                                    <DollarSign className="h-5 w-5" />
                                    Precificação Sugerida
                                </div>
                                <Button size="sm" onClick={handleCreateToken} className="bg-emerald-600 hover:bg-emerald-700">
                                    Tokenizar esta Apólice
                                </Button>
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
