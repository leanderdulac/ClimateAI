#!/usr/bin/env tsx

// Teste simples para verificar dados históricos
import { EmbrapaAPI } from './src/lib/embrapaApi.ts';

async function testHistoricalData() {
  console.log('🧪 Testando dados históricos...');

  const api = new EmbrapaAPI();

  try {
    // Coordenadas de São Paulo
    const latitude = -23.5505;
    const longitude = -46.6333;

    console.log('📍 Testando com coordenadas:', { latitude, longitude });

    // Testar dados históricos de janeiro 2023
    const historicalData = await api.getClimateData(
      latitude,
      longitude,
      '2023-01-01',
      '2023-01-31'
    );

    console.log('✅ Dados históricos recebidos:', historicalData.length, 'registros');

    if (historicalData.length > 0) {
      console.log('📊 Primeiro registro:', historicalData[0]);
      console.log('📊 Último registro:', historicalData[historicalData.length - 1]);
    }

    // Testar análise de risco histórico
    const riskIndex = await api.getHistoricalRiskIndex(latitude, longitude, 5);
    console.log('🎯 Índice de risco histórico (5 anos):', riskIndex);

  } catch (error) {
    console.error('❌ Erro ao testar dados históricos:', error);
  }
}

testHistoricalData();