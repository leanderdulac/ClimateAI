import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { DollarSign, Calculator, AlertTriangle, TrendingUp, Activity } from "lucide-react";

// Mock actuarial calculation function
const calculatePremium = (frequency: number, severity: number, confidence: number) => {
  // Simplified Monte Carlo simulation
  const simulations = 10000;
  let totalLoss = 0;
  
  for (let i = 0; i < simulations; i++) {
    // Simple model: loss occurs with 'frequency' probability
    // Loss amount is random between 0 and 'severity'
    if (Math.random() < frequency / 100) {
      totalLoss += Math.random() * severity;
    }
  }
  
  const averageLoss = totalLoss / simulations;
  // Add confidence margin
  return averageLoss * (1 + (100 - confidence) / 100);
};

export function PricingSimulator() {
  const [frequency, setFrequency] = useState<number>(10); // %
  const [severity, setSeverity] = useState<number>(10000); // $
  const [confidence, setConfidence] = useState<number>(95); // %
  const [premium, setPremium] = useState<number>(0);
  
  const handleCalculate = () => {
    const calculatedPremium = calculatePremium(frequency, severity, confidence);
    setPremium(calculatedPremium);
  };

  return (
    <Card className="overflow-hidden animate-fade-in" variant="default">
      <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Calculator className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Risk Pricing</CardTitle>
              <CardDescription className="text-primary-100">
                Actuarial model for climate risk assessment
              </CardDescription>
            </div>
          </div>
          {premium > 0 && (
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <DollarSign className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">Estimated Premium</div>
                <div className="text-lg font-semibold text-white">
                  ${premium.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-8 p-6 bg-gradient-to-b from-white to-neutral-50">
        <div className="grid gap-8 sm:grid-cols-2">
          <div className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label 
                  htmlFor="frequency" 
                  className="flex items-center gap-2 text-sm font-medium text-neutral-700"
                >
                  <Activity className="h-4 w-4 text-primary-500" />
                  Event Frequency
                </Label>
                <Badge variant="default" className="px-2 py-1">
                  {frequency}%
                </Badge>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4">
                <Slider
                  id="frequency"
                  min={0}
                  max={100}
                  step={1}
                  value={[frequency]}
                  onValueChange={([value]) => setFrequency(value)}
                />
                <div className="mt-2 flex justify-between">
                  <span className="text-xs text-neutral-500">Rare Events</span>
                  <span className="text-xs text-neutral-500">Frequent Events</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label 
                  htmlFor="severity" 
                  className="flex items-center gap-2 text-sm font-medium text-neutral-700"
                >
                  <AlertTriangle className="h-4 w-4 text-warning-500" />
                  Maximum Severity
                </Label>
                <Badge variant="warning" className="px-2 py-1">
                  ${severity.toLocaleString()}
                </Badge>
              </div>
              <Input
                id="severity"
                type="number"
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                variant="outlined"
                className="text-center"
              />
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label 
                  htmlFor="confidence" 
                  className="flex items-center gap-2 text-sm font-medium text-neutral-700"
                >
                  <TrendingUp className="h-4 w-4 text-primary-500" />
                  Confidence Level
                </Label>
                <Badge variant="secondary" className="px-2 py-1">
                  {confidence}%
                </Badge>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4">
                <Slider
                  id="confidence"
                  min={50}
                  max={99}
                  step={1}
                  value={[confidence]}
                  onValueChange={([value]) => setConfidence(value)}
                />
                <div className="mt-2 flex justify-between">
                  <span className="text-xs text-neutral-500">50% (More Risk)</span>
                  <span className="text-xs text-neutral-500">99% (More Safety)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8">
            <div className="rounded-lg border-2 border-dashed border-neutral-200 bg-neutral-50 p-6">
              <div className="space-y-4 text-center">
                <Calculator className="mx-auto h-8 w-8 text-primary-400" />
                <div>
                  <h3 className="text-sm font-semibold text-neutral-900">Risk Assessment</h3>
                  <p className="mt-1 text-xs text-neutral-500">
                    Our actuarial model uses Monte Carlo simulation with {premium === 0 ? '10,000' : '10,000+'} iterations
                  </p>
                </div>
                <Button 
                  onClick={handleCalculate}
                  className="w-full shadow-sm bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white"
                  size="lg"
                >
                  <Calculator className="mr-2 h-4 w-4" />
                  Calculate Premium
                </Button>
              </div>
            </div>

            {premium > 0 && (
              <div className="mt-6 animate-slide-up rounded-lg bg-gradient-to-r from-success-50 to-success-100 p-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="rounded-full bg-success-100 p-2">
                        <DollarSign className="h-4 w-4 text-success-600" />
                      </div>
                      <h3 className="font-medium text-success-900">Premium Estimate</h3>
                    </div>
                    <Badge variant="secondary" className="px-2 py-1">
                      {confidence}% Confidence
                    </Badge>
                  </div>
                  
                  <div className="text-3xl font-bold text-success-700">
                    ${premium.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="text-xs text-neutral-600">Event Frequency</div>
                      <div className="text-lg font-bold text-primary-600">{frequency}%</div>
                    </div>
                    <div className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="text-xs text-neutral-600">Max Severity</div>
                      <div className="text-lg font-bold text-warning-600">${severity.toLocaleString()}</div>
                    </div>
                    <div className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="text-xs text-neutral-600">Confidence</div>
                      <div className="text-lg font-bold text-success-600">{confidence}%</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}