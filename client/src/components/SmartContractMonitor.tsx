import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Activity, AlertTriangle, CheckCircle, Clock, Package, Eye, TrendingUp, Calendar, DollarSign, Plus } from 'lucide-react';
import { useState, useMemo } from 'react';
import { format, addMonths } from 'date-fns';
import { ptBR, enUS, es, zhCN } from 'date-fns/locale';
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTranslation } from "@/hooks/useTranslation";
import { Language } from "@/i18n/translations";

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
  const { t, language } = useTranslation();
  const [startDate, setStartDate] = useState<Date>();
  const [protectionPeriod, setProtectionPeriod] = useState("3");
  const [showNewContract, setShowNewContract] = useState(false);

  // Map app language to date-fns locale
  const dateLocale = useMemo(() => {
    switch (language as Language) {
      case 'pt-BR': return ptBR;
      case 'es-419': return es;
      case 'zh-CN': return zhCN;
      default: return enUS;
    }
  }, [language]);

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

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return t('smartContract.status.active');
      case 'monitoring': return t('smartContract.status.pending');
      case 'settled': return t('smartContract.status.triggered');
      default: return t('smartContract.status.expired');
    }
  };

  const formatDate = (date: string | Date) => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;

    // Different format for Chinese to follow locale standards
    if (language === 'zh-CN') {
      return format(dateObj, "yyyy'年'MM'月'dd'日'", { locale: dateLocale });
    }

    return format(dateObj, "dd 'de' MMMM 'de' yyyy", { locale: dateLocale })
      .replace('de', language === 'pt-BR' ? 'de' : language === 'es-419' ? 'de' : 'of');
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
                {t('smartContract.title')}
              </CardTitle>
              <CardDescription className="text-indigo-100/80">
                {t('smartContract.description')}
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
            {t('smartContract.newContract')}
          </Button>
        </div>

        {showNewContract && (
          <Card className="mb-6 border-2 border-indigo-200">
            <CardHeader className="bg-indigo-50">
              <CardTitle className="text-lg text-indigo-800">{t('smartContract.newContract')}</CardTitle>
              <CardDescription>{t('smartContract.protectionPeriod')}</CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>{t('smartContract.startDate')}</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                      >
                        <Calendar className="mr-2 h-4 w-4" />
                        {startDate ? formatDate(startDate) : t('common.selectDate')}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <CalendarComponent
                        mode="single"
                        selected={startDate}
                        onSelect={setStartDate}
                        initialFocus
                        locale={dateLocale}
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                <div className="space-y-2">
                  <Label>{t('smartContract.protectionPeriod')}</Label>
                  <Select
                    value={protectionPeriod}
                    onValueChange={setProtectionPeriod}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder={t('common.selectPeriod')} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3">3 {t('common.months')}</SelectItem>
                      <SelectItem value="6">6 {t('common.months')}</SelectItem>
                      <SelectItem value="12">12 {t('common.months')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {startDate && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="text-sm text-blue-600">
                    <p><strong>{t('smartContract.protectionPeriod')}:</strong></p>
                    <p>{t('common.start')}: {formatDate(startDate)}</p>
                    <p>{t('common.end')}: {formatDate(addMonths(startDate, parseInt(protectionPeriod)))}</p>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowNewContract(false)}
                >
                  {t('common.cancel')}
                </Button>
                <Button
                  disabled={!startDate}
                  onClick={() => {
                    setShowNewContract(false);
                  }}
                >
                  {t('smartContract.actions.deploy')}
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
                        {getStatusText(contract.status)}
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
                  {t('common.view')}
                </Button>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="flex items-center gap-2 p-2 bg-indigo-50 rounded-lg">
                  <DollarSign className="h-4 w-4 text-indigo-600" />
                  <div>
                    <div className="text-xs text-gray-600">{t('smartContract.insuredValue')}</div>
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
                    <div className="text-xs text-gray-600">{t('smartContract.status.expired')}</div>
                    <div className="font-medium">{contract.expires}</div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  {t('audit.stats.totalOperations')}: {contract.events} • {t('atlas.panel.lastUpdate')}: {contract.lastUpdate}
                </div>
                <div className="text-sm font-mono text-gray-500">
                  {contract.id}
                </div>
              </div>
            </div>
          ))}
        </div>

        <Button variant="outline" className="w-full mt-6 border-indigo-300 text-indigo-700 hover:bg-indigo-50">
          {t('common.loadMore')}
        </Button>
      </CardContent>
    </Card>
  );
}