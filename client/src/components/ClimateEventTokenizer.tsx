import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useState } from 'react';
import axios from 'axios';
import { Zap, Package, TrendingUp, AlertTriangle, Thermometer, MapPin, Calendar, DollarSign, Loader2 } from "lucide-react";

const API_BASE_URL = 'http://localhost:8000/api/v1/blockchain';

export function ClimateEventTokenizer() {
  const [formData, setFormData] = useState({
    tipo: '',
    latitude: '',
    longitude: '',
    data_inicio: '',
    intensidade: '',
    probabilidade: '',
    descricao: '',
    nivel_alerta: '',
    wallet_address: 'climateai_wallet_test',
    token_supply: 10000,
    decimals: 0
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCreateToken = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      // Validar campos obrigatórios
      if (!formData.tipo || !formData.latitude || !formData.longitude || !formData.data_inicio ||
        !formData.intensidade || !formData.probabilidade || !formData.descricao || !formData.nivel_alerta) {
        throw new Error('Todos os campos são obrigatórios');
      }

      const eventoData = {
        tipo: formData.tipo,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        data_inicio: new Date(formData.data_inicio).toISOString(),
        intensidade: parseFloat(formData.intensidade),
        probabilidade: parseFloat(formData.probabilidade) / 100, // Converter de porcentagem para decimal
        descricao: formData.descricao,
        nivel_alerta: parseInt(formData.nivel_alerta)
      };

      const tokenData = {
        evento: eventoData,
        wallet_address: formData.wallet_address,
        token_supply: formData.token_supply,
        decimals: formData.decimals,
        metadata: {
          created_at: new Date().toISOString(),
          creator: 'ClimateAI Dashboard'
        }
      };

      console.log('Enviando dados para tokenização:', tokenData);

      const response = await axios.post(`${API_BASE_URL}/mint`, tokenData, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        setSuccess(true);
        // Reset form
        setFormData({
          tipo: '',
          latitude: '',
          longitude: '',
          data_inicio: '',
          intensidade: '',
          probabilidade: '',
          descricao: '',
          nivel_alerta: '',
          wallet_address: 'climateai_wallet_test',
          token_supply: 10000,
          decimals: 0
        });
      } else {
        throw new Error(response.data.error || 'Erro ao criar token');
      }

    } catch (error: any) {
      console.error('Erro ao criar token:', error);
      setError(error.response?.data?.detail || error.message || 'Erro ao criar token');
    } finally {
      setLoading(false);
    }
  };

  const getEventTypeIcon = (tipo: string) => {
    const icons = {
      'enchente': <Zap className="h-4 w-4 text-blue-600" />,
      'seca': <Thermometer className="h-4 w-4 text-yellow-600" />,
      'onda_calor': <AlertTriangle className="h-4 w-4 text-red-600" />,
      'geada': <Package className="h-4 w-4 text-purple-600" />
    };
    return icons[tipo as keyof typeof icons] || <AlertTriangle className="h-4 w-4 text-gray-600" />;
  };

  return (
    <Card className="border-0 shadow-2xl bg-gradient-to-br from-white via-blue-50/30 to-purple-50/30">
      <CardHeader className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 text-white rounded-t-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <CardTitle className="text-2xl font-bold">Tokenização de Eventos Climáticos</CardTitle>
              <CardDescription className="text-blue-100">
                Crie tokens únicos representando eventos climáticos específicos
              </CardDescription>
            </div>
          </div>
          <Badge className="bg-white/20 text-white border-white/30">
            ClimateAI Blockchain
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-8 space-y-8">
        {success && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <Zap className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-semibold text-green-800">Token criado com sucesso!</p>
                <p className="text-sm text-green-600">O token foi adicionado à sua carteira.</p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <div>
                <p className="font-semibold text-red-800">Erro ao criar token</p>
                <p className="text-sm text-red-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Event Information */}
          <div className="space-y-6">
            <div>
              <Label htmlFor="tipo" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                {getEventTypeIcon(formData.tipo)}
                Tipo de Evento Climático
              </Label>
              <Select value={formData.tipo} onValueChange={(value) => handleInputChange('tipo', value)}>
                <SelectTrigger className="border-gray-300">
                  <SelectValue placeholder="Selecione o tipo de evento" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="enchente">🌊 Enchente</SelectItem>
                  <SelectItem value="seca">☀️ Seca</SelectItem>
                  <SelectItem value="onda_calor">🔥 Onda de Calor</SelectItem>
                  <SelectItem value="geada">❄️ Geada</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="latitude" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                  <MapPin className="h-4 w-4 text-green-600" />
                  Latitude
                </Label>
                <Input
                  id="latitude"
                  type="number"
                  step="0.000001"
                  placeholder="-23.5505"
                  value={formData.latitude}
                  onChange={(e) => handleInputChange('latitude', e.target.value)}
                  className="border-gray-300"
                />
              </div>

              <div>
                <Label htmlFor="longitude" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                  <MapPin className="h-4 w-4 text-blue-600" />
                  Longitude
                </Label>
                <Input
                  id="longitude"
                  type="number"
                  step="0.000001"
                  placeholder="-46.6333"
                  value={formData.longitude}
                  onChange={(e) => handleInputChange('longitude', e.target.value)}
                  className="border-gray-300"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="data_inicio" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                <Calendar className="h-4 w-4 text-purple-600" />
                Data de Início
              </Label>
              <Input
                id="data_inicio"
                type="datetime-local"
                value={formData.data_inicio}
                onChange={(e) => handleInputChange('data_inicio', e.target.value)}
                className="border-gray-300"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="intensidade" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-orange-600" />
                  Intensidade
                </Label>
                <Input
                  id="intensidade"
                  type="number"
                  step="0.1"
                  placeholder="4.5"
                  value={formData.intensidade}
                  onChange={(e) => handleInputChange('intensidade', e.target.value)}
                  className="border-gray-300"
                />
              </div>

              <div>
                <Label htmlFor="probabilidade" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  Probabilidade (%)
                </Label>
                <Input
                  id="probabilidade"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="85"
                  value={formData.probabilidade}
                  onChange={(e) => handleInputChange('probabilidade', e.target.value)}
                  className="border-gray-300"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="nivel_alerta" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                Nível de Alerta (1-5)
              </Label>
              <Select value={formData.nivel_alerta} onValueChange={(value) => handleInputChange('nivel_alerta', value)}>
                <SelectTrigger className="border-gray-300">
                  <SelectValue placeholder="Selecione o nível" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 - Baixo</SelectItem>
                  <SelectItem value="2">2 - Moderado</SelectItem>
                  <SelectItem value="3">3 - Alto</SelectItem>
                  <SelectItem value="4">4 - Muito Alto</SelectItem>
                  <SelectItem value="5">5 - Extremo</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="descricao" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                <Package className="h-4 w-4 text-blue-600" />
                Descrição do Evento
              </Label>
              <Textarea
                id="descricao"
                placeholder="Descreva detalhadamente o evento climático..."
                value={formData.descricao}
                onChange={(e) => handleInputChange('descricao', e.target.value)}
                className="border-gray-300 min-h-[100px]"
              />
            </div>
          </div>

          {/* Token Configuration */}
          <div className="space-y-6">
            <div className="p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl border border-blue-200">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                Configuração do Token
              </h3>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="wallet_address" className="text-sm font-medium text-gray-700">
                    Endereço da Carteira
                  </Label>
                  <Input
                    id="wallet_address"
                    value={formData.wallet_address}
                    onChange={(e) => handleInputChange('wallet_address', e.target.value)}
                    className="border-gray-300 font-mono text-sm"
                  />
                </div>

                <div>
                  <Label htmlFor="token_supply" className="text-sm font-medium text-gray-700">
                    Suprimento Total de Tokens
                  </Label>
                  <Input
                    id="token_supply"
                    type="number"
                    value={formData.token_supply}
                    onChange={(e) => handleInputChange('token_supply', e.target.value)}
                    className="border-gray-300"
                  />
                </div>

                <div>
                  <Label htmlFor="decimals" className="text-sm font-medium text-gray-700">
                    Casas Decimais
                  </Label>
                  <Input
                    id="decimals"
                    type="number"
                    min="0"
                    max="18"
                    value={formData.decimals}
                    onChange={(e) => handleInputChange('decimals', e.target.value)}
                    className="border-gray-300"
                  />
                </div>
              </div>
            </div>

            {/* Preview */}
            <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Prévia do Token</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Símbolo:</span>
                  <span className="font-medium">
                    {formData.tipo ? formData.tipo.slice(0, 3).toUpperCase() + formData.nivel_alerta + '25' : '---'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Suprimento:</span>
                  <span className="font-medium">{formData.token_supply.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Localização:</span>
                  <span className="font-medium text-sm">
                    {formData.latitude && formData.longitude ?
                      `${parseFloat(formData.latitude).toFixed(2)}°, ${parseFloat(formData.longitude).toFixed(2)}°` :
                      '---'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Severidade:</span>
                  <Badge variant="outline" className={
                    formData.nivel_alerta === '5' ? 'border-red-500 text-red-700' :
                      formData.nivel_alerta === '4' ? 'border-orange-500 text-orange-700' :
                        formData.nivel_alerta === '3' ? 'border-yellow-500 text-yellow-700' :
                          'border-gray-500 text-gray-700'
                  }>
                    Nível {formData.nivel_alerta || '?'}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200">
          <Badge className="bg-blue-100 text-blue-800 border-blue-300">🌡️ Temperatura</Badge>
          <Badge className="bg-green-100 text-green-800 border-green-300">🌧️ Precipitação</Badge>
          <Badge className="bg-purple-100 text-purple-800 border-purple-300">💨 Vento</Badge>
          <Badge className="bg-orange-100 text-orange-800 border-orange-300">🌊 Nível d'água</Badge>
          <Badge className="bg-red-100 text-red-800 border-red-300">⚡ Eventos extremos</Badge>
        </div>

        <Button
          onClick={handleCreateToken}
          disabled={loading}
          className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 hover:from-blue-700 hover:via-purple-700 hover:to-blue-800 text-white py-4 text-lg font-semibold shadow-xl"
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 mr-3 animate-spin" />
              Criando Token...
            </>
          ) : (
            <>
              <Zap className="h-5 w-5 mr-3" />
              Criar Token Climático
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
