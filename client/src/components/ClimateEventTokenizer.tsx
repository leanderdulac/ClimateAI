import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useState } from 'react';
import { Zap, Package, Calendar, TrendingUp, AlertTriangle, Eye, Thermometer, Droplets, Wind } from "lucide-react";

export function ClimateEventTokenizer() {
  const [eventName, setEventName] = useState<string>('');
  const [triggerCondition, setTriggerCondition] = useState<string>('');
  const [tokenAmount, setTokenAmount] = useState<number>(1000);
  const [tokenSymbol, setTokenSymbol] = useState<string>('CLIM');

  const handleCreateToken = () => {
    // In a real implementation, this would interact with a smart contract
    console.log('Creating token:', {
      eventName,
      triggerCondition,
      tokenAmount,
      tokenSymbol
    });
    
    // Show success message (in a real app, this would be a toast notification)
    alert(`Token ${tokenSymbol} created successfully for event: ${eventName}`);
  };

  return (
    <Card className="border-0 shadow-xl bg-gradient-to-br from-yellow-50 to-yellow-100/50">
      <CardHeader className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white rounded-t-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold">Climate Event Tokenizer</CardTitle>
              <CardDescription className="text-yellow-100/80">
                Create tokens for specific climate events
              </CardDescription>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6 space-y-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="event-name" className="text-sm font-medium text-gray-700 flex items-center gap-1">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              Event Name
            </Label>
            <Input
              id="event-name"
              placeholder="e.g., Drought in São Paulo 2024"
              value={eventName}
              onChange={(e) => setEventName(e.target.value)}
              className="border-gray-300"
            />
          </div>
          
          <div>
            <Label htmlFor="trigger" className="text-sm font-medium text-gray-700 flex items-center gap-1">
              <Thermometer className="h-4 w-4 text-red-600" />
              Trigger Condition
            </Label>
            <Input
              id="trigger"
              placeholder="e.g., Rainfall < 50mm/month for 3 consecutive months"
              value={triggerCondition}
              onChange={(e) => setTriggerCondition(e.target.value)}
              className="border-gray-300"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="token-amount" className="text-sm font-medium text-gray-700 flex items-center gap-1">
                <TrendingUp className="h-4 w-4 text-green-600" />
                Token Amount
              </Label>
              <Input
                id="token-amount"
                type="number"
                value={tokenAmount}
                onChange={(e) => setTokenAmount(Number(e.target.value))}
                className="border-gray-300"
              />
            </div>
            
            <div>
              <Label htmlFor="token-symbol" className="text-sm font-medium text-gray-700 flex items-center gap-1">
                <Package className="h-4 w-4 text-blue-600" />
                Token Symbol
              </Label>
              <Input
                id="token-symbol"
                placeholder="e.g., CLIM"
                value={tokenSymbol}
                onChange={(e) => setTokenSymbol(e.target.value.toUpperCase())}
                className="border-gray-300"
              />
            </div>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-2 p-3 bg-yellow-100 rounded-lg">
          <Badge variant="outline" className="bg-white border-yellow-300 text-yellow-700">Temperature Threshold</Badge>
          <Badge variant="outline" className="bg-white border-yellow-300 text-yellow-700">Precipitation</Badge>
          <Badge variant="outline" className="bg-white border-yellow-300 text-yellow-700">Wind Speed</Badge>
          <Badge variant="outline" className="bg-white border-yellow-300 text-yellow-700">Flood Level</Badge>
        </div>
        
        <Button 
          onClick={handleCreateToken} 
          className="w-full bg-gradient-to-r from-yellow-600 to-yellow-700 hover:from-yellow-700 hover:to-yellow-800 text-white"
        >
          <Zap className="h-4 w-4 mr-2" />
          Create Climate Token
        </Button>
      </CardContent>
    </Card>
  );
}