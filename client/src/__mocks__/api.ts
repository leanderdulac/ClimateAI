// Mock API module for tests
export const mockApi = {
  policyPricingApi: {
    calculate: jest.fn().mockResolvedValue({
      is_approved: true,
      status: 'APPROVED_MOCK',
      rejection_reason: null,
      financials: {
        pure_premium: 10000,
        risk_margin: 5000,
        loadings: 15000,
        total_premium: 30000,
        op_claims_cost: 2400,
        op_admin_cost: 1500,
        op_subscription_cost: 150,
        total_operational_costs: 4050,
        net_profit: 1500,
        profit_margin_pct: 5,
        combined_ratio: 85
      },
      decision_flow: 'mock_calculation'
    })
  },
  climateDerivativesApi: {
    calculatePricing: jest.fn().mockResolvedValue({}),
    compareScenarios: jest.fn().mockResolvedValue({}),
    getRiskAnalysis: jest.fn().mockResolvedValue({}),
    validateWithINMET: jest.fn().mockResolvedValue({}),
    analyzeCapitalRequirements: jest.fn().mockResolvedValue({})
  },
  mlApi: {
    predictSinistrality: jest.fn().mockResolvedValue({
      frequency: { prediction: 10, confidence_lower: 5, confidence_upper: 15, unit: 'events/year' },
      severity: { prediction: 5000, confidence_lower: 3000, confidence_upper: 7000, unit: 'USD' },
      method: 'machine_learning',
      confidence_level: '95%'
    }),
    trainModels: jest.fn().mockResolvedValue({}),
    getModelInfo: jest.fn().mockResolvedValue({})
  },
  externalApi: {
    getWeatherData: jest.fn().mockResolvedValue({}),
    getEconomicIndicators: jest.fn().mockResolvedValue({}),
    getCommodityPrices: jest.fn().mockResolvedValue({}),
    getXWeatherForecast: jest.fn().mockResolvedValue({}),
    getRealTimeData: jest.fn().mockResolvedValue({})
  },
  microsegmentationApi: {
    createMicrosegments: jest.fn().mockResolvedValue({}),
    analyzeLocationRisk: jest.fn().mockResolvedValue({}),
    getMicrosegmentationSummary: jest.fn().mockResolvedValue({})
  },
  auditApi: {
    getAuditLogs: jest.fn().mockResolvedValue([]),
    getComplianceReport: jest.fn().mockResolvedValue({}),
    logOperation: jest.fn().mockResolvedValue({}),
    getAlerts: jest.fn().mockResolvedValue({ alerts: [], total_count: 0, limit: 10, offset: 0 }),
    acknowledgeAlert: jest.fn().mockResolvedValue({}),
    resolveAlert: jest.fn().mockResolvedValue({}),
    getAlertStats: jest.fn().mockResolvedValue({}),
    getAlertSummary: jest.fn().mockResolvedValue({})
  },
  pricingApi: {
    calculatePricing: jest.fn().mockResolvedValue({
      final_price: 1200,
      risk_score: 0.5,
      risk_factors: {
        climatic_risk: 0.3,
        economic_risk: 0.2,
        location_risk: 0.1
      },
      recommendations: ['Recommendation 1'],
      compliance_flags: [],
      audit_id: 'mock-audit-id'
    })
  }
};

// Default exports to match the real API structure
export const policyPricingApi = mockApi.policyPricingApi;
export const climateDerivativesApi = mockApi.climateDerivativesApi;
export const mlApi = mockApi.mlApi;
export const externalApi = mockApi.externalApi;
export const microsegmentationApi = mockApi.microsegmentationApi;
export const auditApi = mockApi.auditApi;
export const pricingApi = mockApi.pricingApi;
