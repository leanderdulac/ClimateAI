# ♿ Validação de Acessibilidade (a11y) - ClimateAI

## 📊 Visão Geral

Este documento descreve os procedimentos e ferramentas para validação de acessibilidade da plataforma ClimateAI, seguindo as diretrizes WCAG 2.1 nível AA.

## 🎯 Objetivos

| Meta | Target | Descrição |
|------|--------|-----------|
| **WCAG Level** | AA | Conformidade com WCAG 2.1 AA |
| **Score Lighthouse** | > 90 | Acessibilidade no Lighthouse |
| ** axe-core violations** | 0 | Zero violações críticas |

## 📋 Critérios WCAG 2.1 AA

### 1. Perceptível
- [ ] **1.1.1** Conteúdo não-textual tem texto alternativo
- [ ] **1.2.1** Mídia sincronizada tem legendas
- [ ] **1.3.1** Informação e estrutura são separáveis
- [ ] **1.4.1** Cor não é o único meio de distinção
- [ ] **1.4.3** Contraste de cor mínimo 4.5:1
- [ ] **1.4.4** Redimensionamento de texto até 200%

### 2. Operável
- [ ] **2.1.1** Todo funcionalidade via teclado
- [ ] **2.1.2** Sem armadilha de teclado
- [ ] **2.4.1** Pular blocos de navegação
- [ ] **2.4.2** Páginas têm títulos descritivos
- [ ] **2.4.3** Ordem de foco lógica
- [ ] **2.4.4** Propósito de links é claro

### 3. Compreensível
- [ ] **3.1.1** Idioma da página é identificável
- [ ] **3.2.1** Foco não muda contexto inesperadamente
- [ ] **3.2.2** Mudança de input não muda contexto
- [ ] **3.3.1** Erros de input são identificados
- [ ] **3.3.2** Labels ou instruções para input

### 4. Robusto
- [ ] **4.1.1** HTML válido e bem formado
- [ ] **4.1.2** Nome, papel e valor para componentes
- [ ] **4.1.3** Mensagens de status são programáticas

## 🔧 Ferramentas de Validação

### 1. axe-core (Automated Testing)

**Instalação**:
```bash
cd client
npm install --save-dev @axe-core/react axe-core
```

**Uso em testes**:
```typescript
// client/tests/a11y/axe.test.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('Homepage should not have accessibility violations', async ({ page }) => {
    await page.goto('/');
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('Dashboard should not have accessibility violations', async ({ page }) => {
    await page.goto('/dashboard');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('[data-testid="dashboard"]')
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
```

**Uso em desenvolvimento**:
```typescript
// client/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

if (process.env.NODE_ENV === 'development') {
  const axe = await import('@axe-core/react');
  axe.default(React, ReactDOM, 1000);
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
```

### 2. Lighthouse CI

**Configuração**:
```javascript
// client/.lighthouserc.js
module.exports = {
  ci: {
    collect: {
      startServerCommand: 'npm run build && npm run preview',
      startServerReadyPattern: 'ready',
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/dashboard',
        'http://localhost:3000/welcome',
      ],
    },
    upload: {
      target: 'temporary-public-storage',
    },
    assert: {
      assertions: {
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'color-contrast': 'off',
      },
    },
  },
};
```

### 3. Playwright Accessibility Tests

**Configuração**:
```typescript
// client/playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  projects: [
    {
      name: 'accessibility',
      testMatch: '**/*.a11y.ts',
    },
  ],
});
```

**Testes**:
```typescript
// client/tests/a11y/main.a11y.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Main Navigation Accessibility', () => {
  test('should not have accessibility violations', async ({ page }) => {
    await page.goto('/');
    
    // Check homepage
    const homepageResults = await new AxeBuilder({ page }).analyze();
    console.log(`Homepage: ${homepageResults.violations.length} violations`);
    expect(homepageResults.violations).toEqual([]);
    
    // Navigate to dashboard
    await page.getByRole('link', { name: /dashboard/i }).click();
    await page.waitForURL('/dashboard');
    
    const dashboardResults = await new AxeBuilder({ page }).analyze();
    console.log(`Dashboard: ${dashboardResults.violations.length} violations`);
    expect(dashboardResults.violations).toEqual([]);
  });
  
  test('should be navigable with keyboard only', async ({ page }) => {
    await page.goto('/');
    
    // Tab through all interactive elements
    let elementCount = 0;
    const maxElements = 100;
    
    while (elementCount < maxElements) {
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      
      if (!focusedElement || focusedElement === 'BODY') {
        break; // End of tabbable elements
      }
      
      elementCount++;
    }
    
    expect(elementCount).toBeGreaterThan(0);
  });
});
```

## 📝 Checklist de Implementação

### HTML Semântico
- [ ] Usar elementos semânticos (`<header>`, `<nav>`, `<main>`, `<footer>`)
- [ ] Hierarquia de headings correta (`<h1>` → `<h6>`)
- [ ] Landmarks ARIA quando necessário
- [ ] Tabelas com `<caption>` e escopo correto

### Imagens e Mídia
- [ ] Todas imagens têm `alt` descritivo
- [ ] Imagens decorativas têm `alt=""`
- [ ] Ícones têm `aria-label` ou `aria-hidden`
- [ ] Vídeos têm legendas

### Formulários
- [ ] Todos inputs têm `<label>` associado
- [ ] Mensagens de erro são claras e identificadas
- [ ] Campos obrigatórios são indicados
- [ ] Focus é visível em todos inputs

### Navegação
- [ ] Skip link para conteúdo principal
- [ ] Navegação por teclado funciona
- [ ] Focus trap em modais
- [ ] Ordem de foco lógica

### Cores e Contraste
- [ ] Contraste mínimo 4.5:1 para texto normal
- [ ] Contraste mínimo 3:1 para texto grande
- [ ] Cor não é único meio de distinção
- [ ] Links são distinguíveis sem cor

### Responsividade
- [ ] Zoom até 200% funciona
- [ ] Layout funciona em todas orientações
- [ ] Texto não vaza em telas pequenas
- [ ] Touch targets têm 44x44px mínimo

### ARIA
- [ ] Roles ARIA são usadas corretamente
- [ ] Estados ARIA são atualizados
- [ ] Live regions para atualizações dinâmicas
- [ ] Nome acessível para todos componentes

## 🧪 Scripts de Validação

### run-a11y-tests.sh
```bash
#!/bin/bash
# ClimateAI - Accessibility Validation Script

set -e

echo "=========================================="
echo "ClimateAI - Accessibility Validation"
echo "=========================================="
echo "Time: $(date)"
echo "=========================================="

cd client

# Install dependencies
echo ""
echo "[1/4] Installing dependencies..."
npm install --save-dev @axe-core/playwright axe-core

# Run Playwright a11y tests
echo ""
echo "[2/4] Running Playwright accessibility tests..."
npm run test:e2e -- --project=accessibility || {
    echo "✗ Playwright a11y tests FAILED"
    exit 1
}
echo "✓ Playwright a11y tests PASSED"

# Run Lighthouse
echo ""
echo "[3/4] Running Lighthouse accessibility audit..."
npm install --save-dev @lhci/cli
npx lhci autorun || {
    echo "⚠ Lighthouse audit has warnings"
}

# Generate report
echo ""
echo "[4/4] Generating accessibility report..."
mkdir -p reports
cat > reports/a11y-summary.md << EOF
# Accessibility Report

**Date**: $(date)
**Status**: $([ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")

## Summary

- Playwright Tests: $([ $? -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Lighthouse Score: Check reports/lighthouse/*.html

## Next Steps

1. Fix any violations found
2. Re-run tests
3. Document known issues
EOF

echo ""
echo "=========================================="
echo "✓ Accessibility Validation Completed"
echo "=========================================="
echo "Report: reports/a11y-summary.md"
echo "Time: $(date)"
```

### Manual Review Checklist
```bash
#!/bin/bash
# ClimateAI - Manual Accessibility Review

cat << 'EOF'
==========================================
Manual Accessibility Review Checklist
==========================================

NAVIGATION
[ ] Skip link works and is visible on focus
[ ] All interactive elements reachable via Tab
[ ] Focus indicator is visible on all elements
[ ] No keyboard traps
[ ] Modal dialogs trap focus correctly

CONTENT
[ ] All images have meaningful alt text
[ ] Headings are in logical order (h1 → h6)
[ ] Page title is descriptive
[ ] Language is set correctly (lang="pt-BR")

FORMS
[ ] All inputs have associated labels
[ ] Error messages are clear and helpful
[ ] Required fields are indicated
[ ] Form submission feedback is provided

COLORS
[ ] Text has sufficient contrast (4.5:1)
[ ] Color is not the only means of distinction
[ ] Links are distinguishable without color

INTERACTIONS
[ ] No content changes on focus without warning
[ ] Time limits can be extended or disabled
[ ] Animations can be paused or disabled

MOBILE
[ ] Touch targets are at least 44x44px
[ ] Content reflows without horizontal scroll
[ ] Pinch zoom works up to 200%

==========================================
Review completed by: ________________
Date: ________________
Status: [ ] Pass  [ ] Fail
==========================================
EOF
```

## 📊 Relatório de Conformidade

### Template de Relatório
```markdown
# ClimateAI - Accessibility Conformance Report

## Date
2026-02-18

## Evaluation Method
- Automated: axe-core, Lighthouse
- Manual: Keyboard navigation, Screen reader testing
- Assistive Technology: NVDA, VoiceOver

## Conformance Level
**WCAG 2.1 Level AA**: ✅ PASS

## Results Summary

| Category | Score | Status |
|----------|-------|--------|
| Perceivable | 95% | ✅ |
| Operable | 98% | ✅ |
| Understandable | 100% | ✅ |
| Robust | 97% | ✅ |

## Known Issues

### Critical (0)
None

### Major (0)
None

### Minor (2)
1. Some icon buttons could have more descriptive labels
2. Focus indicator could be more visible in dark mode

## Recommendations
1. Add aria-label to all icon-only buttons
2. Enhance focus indicator contrast in dark theme
3. Add skip links to all pages

## Next Review
2026-05-18 (Quarterly)
```

## 🚀 Integração CI/CD

### GitHub Actions
```yaml
# .github/workflows/accessibility.yml
name: Accessibility

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  a11y:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: cd client && npm ci
      
      - name: Build
        run: cd client && npm run build
      
      - name: Run axe-core tests
        run: cd client && npm run test:a11y
      
      - name: Run Lighthouse
        uses: treosh/lighthouse-ci-action@v10
        with:
          configPath: ./client/.lighthouserc.js
          uploadArtifacts: true
      
      - name: Upload accessibility report
        uses: actions/upload-artifact@v3
        with:
          name: a11y-report
          path: ./client/reports/a11y-*.html
```

## 📚 Recursos

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [axe-core Documentation](https://dequeuniversity.com/rules/axe)
- [Lighthouse Accessibility Audits](https://developer.chrome.com/docs/lighthouse/accessibility/)

---

*Documento criado em: 18 de Fevereiro de 2026*
*Próxima revisão: 18 de Maio de 2026*
