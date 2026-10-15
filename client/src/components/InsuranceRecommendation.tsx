import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useLocation } from '@/lib/LocationContext';
import { loadEmbrapaApi } from '@/lib/loadEmbrapaApi';
import { Shield, Droplets, Sun, Wind, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ClimateDataPoint {
    date: string;
    avgTemp: number;
    maxTemp?: number;
    minTemp?: number;
    rainfall: number;
    windSpeed?: number;
}

interface Recommendation {
    type: string;
    title: string;
    description: string;
    reasoning: string[];
    confidence: number;
    icon: any;
    color: string;
}

export function InsuranceRecommendation() {
    const { selectedLocation, isLoadingLocation } = useLocation();
    const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const analyzeAndRecommend = async () => {
            if (!selectedLocation || isLoadingLocation) return;

            setLoading(true);
            try {
                const embrapaApi = await loadEmbrapaApi();

                // Fetch last 365 days of data for a full year analysis
                const endDate = new Date();
                const startDate = new Date();
                startDate.setDate(startDate.getDate() - 365);

                const historicalData = await embrapaApi.getClimateData(
                    selectedLocation.latitude,
                    selectedLocation.longitude,
                    startDate.toISOString().split('T')[0],
                    endDate.toISOString().split('T')[0]
                );

                const data: ClimateDataPoint[] = historicalData.map(d => ({
                    date: d.date,
                    avgTemp: d.temperature,
                    maxTemp: d.temperature_max,
                    minTemp: d.temperature_min,
                    rainfall: d.precipitation,
                    windSpeed: d.wind_speed || d.windSpeed
                }));

                // Analysis Logic
                const totalRainfall = data.reduce((sum, d) => sum + d.rainfall, 0);
                const heavyRainDays = data.filter(d => d.rainfall > 30).length;
                const dryDays = data.filter(d => d.rainfall < 1).length;
                const hotDays = data.filter(d => (d.maxTemp || d.avgTemp) > 30).length;
                const windyDays = data.filter(d => (d.windSpeed || 0) > 20).length;

                window.dispatchEvent(new CustomEvent('climateai:historical-context', {
                    detail: {
                        days: data.length,
                        totalRainfall,
                        heavyRainDays,
                        dryDays,
                        hotDays,
                        windyDays,
                    },
                }));

                let rec: Recommendation;

                // Decision Tree
                if (dryDays > 200 && hotDays > 50) {
                    rec = {
                        type: 'drought',
                        title: 'Seguro Paramétrico de Seca',
                        description: 'Alta probabilidade de estiagem prolongada detectada nesta região.',
                        reasoning: [
                            `${dryDays} dias sem chuva no último ano`,
                            `${hotDays} dias com temperatura acima de 30°C`,
                            'Padrão histórico indica risco elevado de estresse hídrico'
                        ],
                        confidence: 0.85,
                        icon: Sun,
                        color: 'text-orange-500'
                    };
                } else if (heavyRainDays > 20 || totalRainfall > 2000) {
                    rec = {
                        type: 'flood',
                        title: 'Seguro contra Excesso de Chuvas',
                        description: 'Histórico de precipitação intensa indica risco de alagamentos ou danos às colheitas.',
                        reasoning: [
                            `${heavyRainDays} dias com chuva forte (>30mm)`,
                            `Volume total de chuva: ${totalRainfall.toFixed(0)}mm`,
                            'Frequência de tempestades acima da média regional'
                        ],
                        confidence: 0.9,
                        icon: Droplets,
                        color: 'text-blue-500'
                    };
                } else if (windyDays > 30) {
                    rec = {
                        type: 'wind',
                        title: 'Seguro contra Vendavais',
                        description: 'Região sujeita a ventos fortes frequentes que podem danificar estruturas e plantações.',
                        reasoning: [
                            `${windyDays} dias com ventos fortes (>20km/h)`,
                            'Topografia favorece corredores de vento',
                            'Histórico de rajadas repentinas'
                        ],
                        confidence: 0.75,
                        icon: Wind,
                        color: 'text-slate-500'
                    };
                } else {
                    rec = {
                        type: 'multi',
                        title: 'Seguro Multirrisco Climático',
                        description: 'Clima variável sem um único risco dominante extremo. Cobertura abrangente recomendada.',
                        reasoning: [
                            'Equilíbrio entre dias secos e chuvosos',
                            'Temperaturas dentro da média histórica',
                            'Proteção contra variabilidade climática inesperada'
                        ],
                        confidence: 0.8,
                        icon: Shield,
                        color: 'text-emerald-500'
                    };
                }

                setRecommendation(rec);
            } catch (error) {
                console.error("Error generating recommendation:", error);
            } finally {
                setLoading(false);
            }
        };

        analyzeAndRecommend();
    }, [selectedLocation, isLoadingLocation]);

    if (!selectedLocation || !recommendation) return null;

    const Icon = recommendation.icon;

    return (
        <Card className="cc-card relative overflow-hidden border-border/80 bg-card/60 backdrop-blur-xl">
            <div className={`absolute top-0 left-0 w-1.5 h-full ${recommendation.type === 'drought' ? 'bg-amber-400' : recommendation.type === 'flood' ? 'bg-blue-400' : recommendation.type === 'wind' ? 'bg-slate-400' : 'bg-emerald-400'}`}></div>
            <CardHeader className="cc-header border-border/40">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                    <div className={`rounded-xl border border-border/50 bg-muted/40 p-3 ${recommendation.color}`}>
                        <Icon className="h-8 w-8" />
                    </div>
                    <div>
                        <div className="mb-1 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                            AI
                        </div>
                        <CardTitle className="text-xl font-bold text-foreground">
                            Recomendação Inteligente
                        </CardTitle>
                        <CardDescription>
                            Baseado no histórico climático de {selectedLocation.cidade}
                        </CardDescription>
                    </div>
                    <div className="sm:ml-auto flex flex-col sm:items-end">
                        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Confiança</span>
                        <div className="flex items-center gap-1 font-bold text-emerald-400">
                            <CheckCircle className="h-4 w-4" />
                            {(recommendation.confidence * 100).toFixed(0)}%
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="mb-6">
                    <h3 className={`mb-2 text-2xl font-bold ${recommendation.color}`}>
                        {recommendation.title}
                    </h3>
                    <p className="leading-relaxed text-muted-foreground">
                        {recommendation.description}
                    </p>
                </div>

                <div className="mb-6 rounded-2xl border border-border/50 bg-muted/30 p-4">
                    <h4 className="mb-3 flex items-center gap-2 font-semibold text-foreground">
                        <TrendingUp className="h-4 w-4 text-primary" />
                        Análise de Fatores
                    </h4>
                    <ul className="space-y-2">
                        {recommendation.reasoning.map((reason, index) => (
                            <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
                                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary"></span>
                                {reason}
                            </li>
                        ))}
                    </ul>
                </div>

                <Button
                    className="w-full rounded-full shadow-md shadow-primary/20 group"
                    onClick={() => {
                        window.dispatchEvent(new CustomEvent('climateai:insurance-intent', {
                            detail: {
                                active: true,
                                source: 'insurance-recommendation',
                                recommendationType: recommendation.type,
                                confidence: recommendation.confidence,
                            },
                        }));

                        const element = document.querySelector('.pricing-simulator');
                        if (element) {
                            element.scrollIntoView({ behavior: 'smooth' });
                        }
                    }}
                >
                    Simular este Seguro
                    <Shield className="ml-2 h-4 w-4 group-hover:scale-110 transition-transform" />
                </Button>
            </CardContent>
        </Card>
    );
}
