
export const translations = {
    'pt-BR': {
        // Header
        'app.name': 'ClimateAI',
        'nav.login': 'Entrar / Cadastrar',

        // Hero
        'hero.welcome': 'Bem-vindo ao',
        'hero.description': 'Você chegou ao futuro da modelagem climático-econômica. Nossa plataforma combina inteligência artificial, dados climáticos e modelagem atuarial para ajudar você a tomar decisões mais inteligentes.',
        'hero.cta': 'Começar a Explorar',
        'hero.subtitle': 'Descubra como transformar riscos climáticos em oportunidades',

        // Features
        'feature.analysis.title': 'Análise Climática Avançada',
        'feature.analysis.desc': 'Modelos de IA para previsão de riscos climáticos e impacto econômico',
        'feature.actuarial.title': 'Modelagem Atuarial',
        'feature.actuarial.desc': 'Cálculos precisos de prêmios baseados em dados climáticos históricos',
        'feature.dashboard.title': 'Dashboard Interativo',
        'feature.dashboard.desc': 'Interface intuitiva para visualização de dados e tomada de decisões',

        // Quick Start
        'guide.title': 'Como Começar',
        'guide.step1.title': 'Selecione uma Localização',
        'guide.step1.desc': 'Escolha uma cidade ou região para analisar os dados climáticos e riscos associados.',
        'guide.step2.title': 'Configure o Período',
        'guide.step2.desc': 'Defina o período de análise (7, 30 ou 90 dias) para obter previsões precisas.',
        'guide.step3.title': 'Visualize os Dados',
        'guide.step3.desc': 'Explore gráficos interativos, mapas de risco e métricas de performance.',
        'guide.step4.title': 'Simule Cenários',
        'guide.step4.desc': 'Use nossa calculadora atuarial para simular diferentes cenários de risco.',

        // Footer
        'footer.copyright': '© 2024 ClimateAI. Transformando riscos climáticos em oportunidades.'
    },
    'en-US': {
        // Header
        'app.name': 'ClimateAI',
        'nav.login': 'Login / Sign Up',

        // Hero
        'hero.welcome': 'Welcome to',
        'hero.description': 'You have arrived at the future of climate-economic modeling. Our platform combines artificial intelligence, climate data, and actuarial modeling to help you make smarter decisions.',
        'hero.cta': 'Start Exploring',
        'hero.subtitle': 'Discover how to transform climate risks into opportunities',

        // Features
        'feature.analysis.title': 'Advanced Climate Analysis',
        'feature.analysis.desc': 'AI models for climate risk prediction and economic impact',
        'feature.actuarial.title': 'Actuarial Modeling',
        'feature.actuarial.desc': 'Precise premium calculations based on historical climate data',
        'feature.dashboard.title': 'Interactive Dashboard',
        'feature.dashboard.desc': 'Intuitive interface for data visualization and decision making',

        // Quick Start
        'guide.title': 'How to Start',
        'guide.step1.title': 'Select a Location',
        'guide.step1.desc': 'Choose a city or region to analyze climate data and associated risks.',
        'guide.step2.title': 'Configure Period',
        'guide.step2.desc': 'Define the analysis period (7, 30, or 90 days) to get accurate forecasts.',
        'guide.step3.title': 'Visualize Data',
        'guide.step3.desc': 'Explore interactive charts, risk maps, and performance metrics.',
        'guide.step4.title': 'Simulate Scenarios',
        'guide.step4.desc': 'Use our actuarial calculator to simulate different risk scenarios.',

        // Footer
        'footer.copyright': '© 2024 ClimateAI. Transforming climate risks into opportunities.'
    }
};

export type Language = 'pt-BR' | 'en-US';
export type TranslationKey = keyof typeof translations['en-US'];
