import React, { useState, useRef, useEffect } from 'react';
import { geminiApi, embrapaApi, policyPricingApi } from '../lib/api';
import { useLocation } from '../lib/LocationContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { MessageCircle, X, Send, Loader2, Minimize2, Maximize2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export function ClimateAssistant() {
    const [isOpen, setIsOpen] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);
    const { selectedLocation } = useLocation();
    const [weatherData, setWeatherData] = useState<any>(null);
    const [microclimateData, setMicroclimateData] = useState<any>(null);
    const [policyCost, setPolicyCost] = useState<number | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const lastAnalyzedLocation = useRef<string | null>(null);

    // Enhanced microclimate analysis and policy cost estimation
    useEffect(() => {
        if (selectedLocation) {
            const locationId = `${selectedLocation.latitude},${selectedLocation.longitude}`;

            // Avoid re-analyzing the same location
            if (lastAnalyzedLocation.current === locationId) return;

            const fetchDetailedData = async () => {
                setIsLoading(true);
                try {
                    // Fetch current weather data
                    const data = await embrapaApi.getDadosAtuais(selectedLocation.latitude, selectedLocation.longitude);
                    setWeatherData(data);

                    // Fetch 365 days of historical data for microclimate analysis
                    const endDate = new Date();
                    const startDate = new Date();
                    startDate.setDate(startDate.getDate() - 365);

                    const historicalData = await embrapaApi.getClimateData(
                        selectedLocation.latitude,
                        selectedLocation.longitude,
                        startDate.toISOString().split('T')[0],
                        endDate.toISOString().split('T')[0]
                    );

                    // Analyze historical data for microclimate patterns
                    const totalRainfall = historicalData.reduce((sum, d) => sum + d.precipitation, 0);
                    const heavyRainDays = historicalData.filter(d => d.precipitation > 30).length;
                    const dryDays = historicalData.filter(d => d.precipitation < 1).length;
                    const hotDays = historicalData.filter(d => d.temperature > 30).length;
                    const windyDays = historicalData.filter(d => (d.vento_velocidade || 0) > 20).length;

                    // Determine microclimate type based on historical patterns
                    let microclimateType = 'normal';
                    if (dryDays > 200 && hotDays > 50) {
                        microclimateType = 'arid';
                    } else if (heavyRainDays > 20 || totalRainfall > 2000) {
                        microclimateType = 'humid';
                    } else if (windyDays > 30) {
                        microclimateType = 'windy';
                    } else if (selectedLocation.cidade?.toLowerCase().includes('serra') ||
                               selectedLocation.cidade?.toLowerCase().includes('alto') ||
                               (selectedLocation.latitude && Math.abs(selectedLocation.latitude) > 1000)) { // High altitude indicator
                        microclimateType = 'montanha';
                    }

                    // Create microclimate analysis data
                    const microclimateInfo = {
                        type: microclimateType,
                        totalRainfall,
                        heavyRainDays,
                        dryDays,
                        hotDays,
                        windyDays,
                        temperatureRange: {
                            min: Math.min(...historicalData.map(d => d.temperature)),
                            max: Math.max(...historicalData.map(d => d.temperature)),
                            avg: historicalData.reduce((sum, d) => sum + d.temperature, 0) / historicalData.length,
                        }
                    };

                    setMicroclimateData(microclimateInfo);
                    lastAnalyzedLocation.current = locationId;

                    // Proactive Analysis with concise message
                    const context = {
                        page: window.location.pathname,
                        timestamp: new Date().toISOString(),
                        location: {
                            city: selectedLocation.cidade,
                            state: selectedLocation.estado,
                            latitude: selectedLocation.latitude,
                            longitude: selectedLocation.longitude
                        },
                        weather: {
                            temp: data.temperatura,
                            precip: data.precipitacao,
                            humidity: data.umidade,
                            wind: data.vento_velocidade
                        },
                        microclimate: {
                            type: microclimateType,
                            characteristics: getMicroclimateCharacteristics(microclimateType),
                            historicalData: microclimateInfo
                        }
                    };

                    const systemInstruction = `
                        O usuário selecionou a localização: ${selectedLocation.cidade}, ${selectedLocation.estado}.
                        Dados climáticos atuais: Temperatura ${data.temperatura}°C, Precipitação ${data.precipitacao}mm, Umidade ${data.umidade}%.

                        Microclima local: ${getMicroclimateDescription(microclimateType)}

                        Forneça uma análise direta e útil, mencionando brevemente a cidade e evitando introduções longas.
                        Baseie-se nos dados de microclima para sugerir o tipo de seguro mais apropriado.
                    `;

                    const response = await geminiApi.chat(systemInstruction, context);

                    const assistantMessage: Message = {
                        id: Date.now().toString(),
                        role: 'assistant',
                        content: response.response,
                        timestamp: new Date()
                    };

                    setMessages(prev => {
                        // Remove generic welcome if it exists
                        const filtered = prev.filter(m => m.id !== 'welcome');
                        return [...filtered, assistantMessage];
                    });

                } catch (error) {
                    console.error('Error fetching microclimate/analysis:', error);
                } finally {
                    setIsLoading(false);
                }
            };
            fetchDetailedData();
        }
    }, [selectedLocation]);

    // Helper function to get microclimate descriptions
    const getMicroclimateDescription = (type: string) => {
        switch(type) {
            case 'arid': return 'Zona árida com alta frequência de dias sem chuva e temperaturas elevadas';
            case 'humid': return 'Zona úmida com alta precipitação e risco de alagamentos';
            case 'windy': return 'Zona com ventos fortes frequentes';
            case 'montanha': return 'Zona de montanha com microclima específico de altitude';
            default: return 'Microclima típico da região';
        }
    };

    // Helper function to get microclimate characteristics
    const getMicroclimateCharacteristics = (type: string) => {
        switch(type) {
            case 'arid':
                return ['Alta evapotranspiração', 'Risco de estiagem', 'Necessidade de irrigação', 'Maior variabilidade térmica'];
            case 'humid':
                return ['Alta precipitação', 'Risco de encharcamento', 'Maior umidade do solo', 'Menor amplitude térmica'];
            case 'windy':
                return ['Ventos fortes frequentes', 'Risco de danos estruturais', 'Evapotranspiração elevada', 'Dificuldade na aplicação de defensivos'];
            case 'montanha':
                return ['Altitude elevada', 'Maior amplitude térmica', 'Formação de geadas', 'Correntes de ar específicas'];
            default:
                return ['Clima temperado', 'Precipitação moderada', 'Condições típicas da região'];
        }
    };

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollAreaRef.current) {
            scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
        }
    }, [messages, isOpen, isMinimized]);

    const handleSendMessage = async () => {
        if (!inputValue.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            // Build rich context with microclimate data and historical analysis
            const context = {
                page: window.location.pathname,
                timestamp: new Date().toISOString(),
                location: selectedLocation ? {
                    city: selectedLocation.cidade,
                    state: selectedLocation.estado,
                    latitude: selectedLocation.latitude,
                    longitude: selectedLocation.longitude
                } : null,
                weather: weatherData ? {
                    temp: weatherData.temperatura,
                    precip: weatherData.precipitacao,
                    humidity: weatherData.umidade,
                    wind: weatherData.vento_velocidade
                } : null,
                microclimate: microclimateData ? {
                    type: microclimateData.type,
                    characteristics: getMicroclimateCharacteristics(microclimateData.type),
                    historicalData: microclimateData
                } : null
            };

            // Send to Gemini with context AND history
            const response = await geminiApi.chat(inputValue, context, messages);

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.response,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Failed to send message:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'Desculpe, encontrei um erro ao processar sua mensagem. Por favor, tente novamente.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    if (!isOpen) {
        return (
            <Button
                className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg z-50 bg-primary hover:bg-primary/90 transition-all duration-300 hover:scale-110"
                onClick={() => setIsOpen(true)}
            >
                <MessageCircle className="h-8 w-8 text-white" />
            </Button>
        );
    }

    return (
        <Card className={`fixed bottom-6 right-6 shadow-2xl z-50 transition-all duration-300 flex flex-col ${isMinimized ? 'w-72 h-14' : 'w-[400px] h-[600px]'}`}>
            <CardHeader className="p-4 bg-primary text-primary-foreground rounded-t-lg flex flex-row items-center justify-between space-y-0 cursor-pointer" onClick={() => setIsMinimized(!isMinimized)}>
                <div className="flex items-center gap-2">
                    <MessageCircle className="h-5 w-5" />
                    <CardTitle className="text-base font-medium">Climate Assistant</CardTitle>
                </div>
                <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-primary-foreground hover:bg-primary-foreground/20" onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }}>
                        {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-primary-foreground hover:bg-primary-foreground/20" onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}>
                        <X className="h-4 w-4" />
                    </Button>
                </div>
            </CardHeader>

            {!isMinimized && (
                <>
                    <CardContent className="flex-1 p-0 overflow-hidden bg-background">
                        <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
                            <div className="flex flex-col gap-4 pb-4">
                                {messages.map((msg) => (
                                    <div
                                        key={msg.id}
                                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div
                                            className={`max-w-[85%] rounded-lg px-4 py-2 text-sm ${msg.role === 'user'
                                                ? 'bg-primary text-primary-foreground'
                                                : 'bg-muted text-foreground'
                                                }`}
                                        >
                                            <div className="prose prose-sm dark:prose-invert max-w-none">
                                                <ReactMarkdown>
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
                                            <span className="text-[10px] opacity-70 block mt-1 text-right">
                                                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                                {isLoading && (
                                    <div className="flex justify-start">
                                        <div className="bg-muted rounded-lg px-4 py-2 flex items-center gap-2">
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            <span className="text-xs text-muted-foreground">Digitando...</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </ScrollArea>
                    </CardContent>
                    <CardFooter className="p-3 border-t bg-background rounded-b-lg">
                        <div className="flex w-full gap-2">
                            <Input
                                placeholder="Digite sua mensagem..."
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                disabled={isLoading}
                                className="flex-1"
                            />
                            <Button size="icon" onClick={handleSendMessage} disabled={isLoading || !inputValue.trim()}>
                                <Send className="h-4 w-4" />
                            </Button>
                        </div>
                    </CardFooter>
                </>
            )}
        </Card>
    );
}
