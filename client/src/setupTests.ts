// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// JSDOM does not provide IntersectionObserver by default.
class MockIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (!(globalThis as { IntersectionObserver?: unknown }).IntersectionObserver) {
  (globalThis as { IntersectionObserver?: typeof MockIntersectionObserver }).IntersectionObserver = MockIntersectionObserver;
}

// Mock all API calls to prevent tests from making real network requests
// This is especially important when backend service may not be available during CI/CD
vi.mock('./lib/api', () => ({
  buildApiUrl: vi.fn((path: string) => `http://localhost:8000${path.startsWith('/') ? path : `/${path}`}`),
  policyPricingApi: {
    calculate: vi.fn().mockResolvedValue({
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
    calculatePricing: vi.fn().mockResolvedValue({}),
    compareScenarios: vi.fn().mockResolvedValue({}),
    getRiskAnalysis: vi.fn().mockResolvedValue({}),
    validateWithINMET: vi.fn().mockResolvedValue({}),
    analyzeCapitalRequirements: vi.fn().mockResolvedValue({})
  },
  mlApi: {
    predictSinistrality: vi.fn().mockResolvedValue({
      frequency: { prediction: 10, confidence_lower: 5, confidence_upper: 15, unit: 'events/year' },
      severity: { prediction: 5000, confidence_lower: 3000, confidence_upper: 7000, unit: 'USD' },
      method: 'machine_learning',
      confidence_level: '95%'
    }),
    trainModels: vi.fn().mockResolvedValue({}),
    getModelInfo: vi.fn().mockResolvedValue({})
  },
  externalApi: {
    getWeatherData: vi.fn().mockResolvedValue({}),
    getEconomicIndicators: vi.fn().mockResolvedValue({}),
    getCommodityPrices: vi.fn().mockResolvedValue({}),
    getXWeatherForecast: vi.fn().mockResolvedValue({}),
    getRealTimeData: vi.fn().mockResolvedValue({})
  },
  microsegmentationApi: {
    createMicrosegments: vi.fn().mockResolvedValue({}),
    analyzeLocationRisk: vi.fn().mockResolvedValue({}),
    getMicrosegmentationSummary: vi.fn().mockResolvedValue({})
  },
  auditApi: {
    getAuditLogs: vi.fn().mockResolvedValue([]),
    getComplianceReport: vi.fn().mockResolvedValue({}),
    logOperation: vi.fn().mockResolvedValue({}),
    getAlerts: vi.fn().mockResolvedValue({ alerts: [], total_count: 0, limit: 10, offset: 0 }),
    acknowledgeAlert: vi.fn().mockResolvedValue({}),
    resolveAlert: vi.fn().mockResolvedValue({}),
    getAlertStats: vi.fn().mockResolvedValue({}),
    getAlertSummary: vi.fn().mockResolvedValue({})
  },
  pricingApi: {
    calculatePricing: vi.fn().mockResolvedValue({
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
}));

// Suppress known expected unhandled rejections from AuthContext
// login() and register() intentionally re-throw errors after setting state.
// When triggered via button click in tests, this becomes an unhandled rejection.
const knownAuthErrorMessages = [
  'Falha de conexao',
  'Service unavailable',
  'Falha no login',
  'Falha no cadastro',
];

// Handle via window for jsdom env
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (event) => {
    if (knownAuthErrorMessages.some(msg => event.reason?.message?.includes(msg))) {
      event.preventDefault();
    }
  });
}

// Handle via process for Vitest's node-side rejection tracking
if (typeof process !== 'undefined') {
  process.on('unhandledRejection', (reason) => {
    const message = reason instanceof Error ? reason.message : String(reason ?? '');
    if (knownAuthErrorMessages.some(msg => message.includes(msg))) {
      // Suppress — these are expected re-throws from AuthContext button click handlers
      return;
    }
  });
}


