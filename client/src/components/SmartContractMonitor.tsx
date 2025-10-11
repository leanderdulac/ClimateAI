import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Activity, AlertTriangle, CheckCircle, Clock, Package, Eye, TrendingUp, Calendar, DollarSign, Plus } from 'lucide-react';
import { useState } from 'react';
import { format, addMonths } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Mock data for smart contracts
const contractData = [
  {
    id: '0x1a2b3c...',
    name: 'Drought Protection - São Paulo',
    status: 'active',
    trigger: 'Rainfall < 50mm/month',
    payout: '$25,000',
    lastUpdate: '2023-06-15',
    events: 2,
    roi: '12.5%',
    expires: '2024-12-31'
  },
  {
    id: '0x4d5e6f...',
    name: 'Flood Coverage - Rio de Janeiro',
    status: 'monitoring',
    trigger: 'Water level > 3m',
    payout: '$15,000',
    lastUpdate: '2023-06-14',
    events: 0,
    roi: '8.3%',
    expires: '2024-10-15'
  },
  {
    id: '0x7g8h9i...',
    name: 'Temperature Anomaly - Brasília',
    status: 'settled',
    trigger: 'Temp > 38°C for 5 days',
    payout: '$8,500',
    lastUpdate: '2023-06-10',
    events: 1,
    roi: 'Claimed',
    expires: '2023-09-30'
  }
];

export function SmartContractMonitor() {
  const [startDate, setStartDate] = useState<Date>();
  const [protectionPeriod, setProtectionPeriod] = useState("3");
  const [showNewContract, setShowNewContract] = useState(false);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Activity className="h-4 w-4 text-green-600" />;
      case 'monitoring':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'settled':
        return <CheckCircle className="h-4 w-4 text-blue-600" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
    }
  };

  const formatDate = (date: string | Date) => {
    if (typeof date === 'string') {
      return format(new Date(date), "dd 'de' MMMM 'de' yyyy", { locale: ptBR });
    }
    return format(date, "dd 'de' MMMM 'de' yyyy", { locale: ptBR });
  };

  return (
    <Card className="border-0 shadow-xl bg-gradient-to-br from-indigo-50 to-indigo-100/50">
      <CardHeader className="bg-gradient-to-r from-indigo-500 to-indigo-600 text-white rounded-t-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Package className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Smart Contract Monitor
              </CardTitle>
              <CardDescription className="text-indigo-100/80">
                Real-time monitoring of climate derivative contracts
              </CardDescription>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="flex justify-between items-center mb-6">
          <Button
            variant="outline"
            className="border-indigo-300 text-indigo-700 hover:bg-indigo-50"
            onClick={() => setShowNewContract(!showNewContract)}
          >
            <Plus className="h-4 w-4 mr-2" />
            Novo Contrato de Proteção
          </Button>
        </div>

        {showNewContract && (
          <Card className="mb-6 border-2 border-indigo-200">
            <CardHeader className="bg-indigo-50">
              <CardTitle className="text-lg text-indigo-800">Novo Contrato de Proteção Climática</CardTitle>
              <CardDescription>Defina o período de proteção do seu seguro</CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Data de Início</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                      >
                        <Calendar className="mr-2 h-4 w-4" />
                        {startDate ? formatDate(startDate) : "Selecione a data de início"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <CalendarComponent
                        mode="single"
                        selected={startDate}
                        onSelect={setStartDate}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                <div className="space-y-2">
                  <Label>Período de Proteção</Label>
                  <Select
                    value={protectionPeriod}
                    onValueChange={setProtectionPeriod}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Selecione o período" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3">3 meses</SelectItem>
                      <SelectItem value="6">6 meses</SelectItem>
                      <SelectItem value="12">12 meses</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {startDate && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="text-sm text-blue-600">
                    <p><strong>Período de Cobertura:</strong></p>
                    <p>Início: {formatDate(startDate)}</p>
                    <p>Fim: {formatDate(addMonths(startDate, parseInt(protectionPeriod)))}</p>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowNewContract(false)}
                >
                  Cancelar
                </Button>
                <Button
                  disabled={!startDate}
                  onClick={() => {
                    // Aqui implementaremos a criação do contrato
                    setShowNewContract(false);
                  }}
                >
                  Criar Contrato
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="space-y-4">
          {contractData.map((contract) => (
            <div
              key={contract.id}
              className="p-5 bg-white rounded-xl border border-indigo-200 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-lg text-gray-800">{contract.name}</h3>
                    <Badge className={`${contract.status === 'active' ? 'bg-green-500' :
                      contract.status === 'monitoring' ? 'bg-yellow-500' :
                        'bg-blue-500'
                      } text-white`}>
                      <span className="flex items-center gap-1">
                        {getStatusIcon(contract.status)}
                        {contract.status.charAt(0).toUpperCase() + contract.status.slice(1)}
                      </span>
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600">
                    <AlertTriangle className="h-4 w-4 inline mr-1 text-orange-600" />
                    {contract.trigger}
                  </p>
                </div>
                <Button variant="outline" size="sm" className="border-indigo-300 text-indigo-700 hover:bg-indigo-50">
                  <Eye className="h-4 w-4 mr-1" />
                  View
                </Button>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="flex items-center gap-2 p-2 bg-indigo-50 rounded-lg">
                  <DollarSign className="h-4 w-4 text-indigo-600" />
                  <div>
                    <div className="text-xs text-gray-600">Payout</div>
                    <div className="font-medium">{contract.payout}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 p-2 bg-indigo-50 rounded-lg">
                  <TrendingUp className="h-4 w-4 text-green-600" />
                  <div>
                    <div className="text-xs text-gray-600">ROI</div>
                    <div className="font-medium">{contract.roi}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 p-2 bg-indigo-50 rounded-lg">
                  <Calendar className="h-4 w-4 text-blue-600" />
                  <div>
                    <div className="text-xs text-gray-600">Expires</div>
                    <div className="font-medium">{contract.expires}</div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  Events: {contract.events} • Updated: {contract.lastUpdate}
                </div>
                <div className="text-sm font-mono text-gray-500">
                  {contract.id}
                </div>
              </div>
            </div>
          ))}
        </div>

        <Button variant="outline" className="w-full mt-6 border-indigo-300 text-indigo-700 hover:bg-indigo-50">
          Load More Contracts
        </Button>
      </CardContent>
    </Card>
  );
}