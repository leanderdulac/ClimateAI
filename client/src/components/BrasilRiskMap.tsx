import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// ...existing code...
import { MapPin } from "lucide-react";

export function BrasilRiskMap() {
    const regions = [
        { name: "Sudeste", risk: "Médio", color: "bg-orange-500", percent: 45 },
        { name: "Sul", risk: "Baixo", color: "bg-green-500", percent: 20 },
        { name: "Nordeste", risk: "Alto", color: "bg-red-500", percent: 75 },
        { name: "Norte", risk: "Médio", color: "bg-yellow-500", percent: 30 },
        { name: "Centro-Oeste", risk: "Baixo", color: "bg-green-500", percent: 15 },
    ];

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-primary" />
                    Distribuição de Risco por Região (Brasil)
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {regions.map((reg) => (
                        <div key={reg.name} className="flex items-center justify-between">
                            <div className="flex flex-col">
                                <span className="text-sm font-medium">{reg.name}</span>
                                <span className="text-xs text-muted-foreground">Risco: {reg.risk}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${reg.color}`}
                                        style={{ width: `${reg.percent}%` }}
                                    />
                                </div>
                                <span className="text-xs font-bold w-8">{reg.percent}%</span>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
