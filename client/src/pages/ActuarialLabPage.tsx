import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DashboardLayout } from "@/components/DashboardLayout";
import { ParametricSimulator } from "@/components/ParametricSimulator";
import { HybridParametricSimulator } from "@/components/HybridParametricSimulator";
import { FlaskConical, History, Lightbulb } from "lucide-react";

export function ActuarialLabPage() {
    return (
        <DashboardLayout
            title="Lab Atuarial"
            subtitle="Design e Backtesting de Contratos Paramétricos"
        >
            <Tabs defaultValue="theory" className="space-y-6">
                <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
                    <TabsTrigger value="theory" className="flex items-center gap-2">
                        <Lightbulb className="h-4 w-4" />
                        Design Teórico
                    </TabsTrigger>
                    <TabsTrigger value="history" className="flex items-center gap-2">
                        <History className="h-4 w-4" />
                        Backtesting (CEMADEN)
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="theory" className="space-y-4">
                    <div className="bg-blue-50/50 border border-blue-100 p-4 rounded-lg mb-4 text-sm text-blue-800 flex gap-3">
                        <FlaskConical className="h-5 w-5 text-blue-600 shrink-0" />
                        <p>Use este simulador para modelar novos gatilhos e calcular VaR/TVaR baseados em distribuições estatísticas teóricas.</p>
                    </div>
                    <ParametricSimulator />
                </TabsContent>

                <TabsContent value="history" className="space-y-4">
                    <div className="bg-emerald-50/50 border border-emerald-100 p-4 rounded-lg mb-4 text-sm text-emerald-800 flex gap-3">
                        <History className="h-5 w-5 text-emerald-600 shrink-0" />
                        <p>Valide seus gatilhos contra dados reais de estações automáticas e satélites do CEMADEN/Open-Meteo.</p>
                    </div>
                    <HybridParametricSimulator />
                </TabsContent>
            </Tabs>
        </DashboardLayout>
    );
}
