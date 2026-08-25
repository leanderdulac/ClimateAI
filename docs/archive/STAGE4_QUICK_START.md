# Quick Start - Executar Testes E2E

## ⚡ 30 Segundos para começar

```bash
cd /home/artha/climateAI/client
npm run test:e2e:ui
```

Isso vai:
1. Iniciar servidor dev (`npm run dev`)
2. Abrir interface visual do Playwright
3. Rodar testes em tempo real
4. Mostrar results com screenshots/videos

---

## 📖 Opções de Execução

| Comando | O que faz | Para quem |
|---------|-----------|----------|
| `npm run test:e2e` | Headless mode | CI/CD, Scripts |
| `npm run test:e2e:ui` | Interface visual | Desenvolvimento |
| `npm run test:e2e:headed` | Browser visível | Debugging |
| `npm run test:e2e:debug` | Debug interativo | Investigação |

---

## 📊 Testes Disponíveis (28 total)

### ✅ auth.spec.ts - Autenticação (6)
- Welcome page loads
- Auth page navigation
- Login form display
- Invalid credentials error
- Email validation
- Accessibility check

### ✅ navigation.spec.ts - Rotas (7)
- Page navigation
- Welcome page
- Navigation menu
- Protected routes
- 404 handling
- Navigation state
- Status codes

### ✅ components.spec.ts - UI (8)
- Component rendering
- Button clicks
- Accessible headings
- Image alt text
- Color contrast
- Window resize
- Form submission
- Semantic HTML

### ✅ performance.spec.ts - Perf (7)
- Load time (< 5s)
- Lazy loading
- Layout shift (< 0.25)
- Console errors
- Bundle efficiency
- Image optimization
- First Contentful Paint

---

## 🎯 Resultado esperado

Todos os 28 testes devem passar ✅

```
auth.spec.ts (6 tests)
  ✓ should display welcome page on initial load
  ✓ should navigate to auth page from welcome page
  ✓ should display login form on auth page
  ✓ should show error with invalid credentials
  ✓ should validate email format
  ✓ should have accessible auth form

navigation.spec.ts (7 tests)
  ✓ should navigate between pages correctly
  ✓ should display welcome page
  ✓ should have navigation menu
  ✓ should handle protected route access
  ✓ should handle 404 gracefully
  ✓ should persist navigation state
  ✓ should load pages with correct status codes

components.spec.ts (8 tests)
  ✓ should render welcome page components
  ✓ should handle button clicks
  ✓ should have accessible headings
  ✓ should render images with alt text
  ✓ should have proper color contrast
  ✓ should handle window resize
  ✓ should handle form submission
  ✓ should have proper semantic HTML

performance.spec.ts (7 tests)
  ✓ should load page within acceptable time
  ✓ should handle lazy loading of pages
  ✓ should render without layout shift
  ✓ should not have console errors on page load
  ✓ should lazy load subpages efficiently
  ✓ should handle images efficiently
  ✓ should measure First Contentful Paint

────────────────────────────────────
28 passed (2m 15s)
```

---

## 🔍 Se algo der errado

### Porta 3000 em uso
```bash
lsof -i :3000
kill -9 <PID>
```

### Testes muito lentos
```bash
# Rodar apenas um teste
npx playwright test auth.spec.ts

# Rodar um navegador
npx playwright test --project=chromium
```

### Precisa de help
```bash
# Ver opções
npx playwright test --help

# Debug mode
npm run test:e2e:debug

# Ver relatório
npx playwright show-report
```

---

## 🚀 Próximas etapas

1. ✅ Executar: `npm run test:e2e:ui`
2. ✅ Confirmar: Todos os 28 testes passam
3. ✅ Documentar: Ver ETAPA4_TESTES_E2E.md para mais detalhes
4. ✅ Integrar: Adicionar em CI/CD pipeline

---

**Docs completo**: [ETAPA4_TESTES_E2E.md](./ETAPA4_TESTES_E2E.md)
**Config**: [playwright.config.ts](./client/playwright.config.ts)
**Testes**: [client/tests/e2e/](./client/tests/e2e/)
