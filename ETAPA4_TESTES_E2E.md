# Testes E2E com Playwright - Etapa 4

## 📋 Resumo

Implementação completa de testes End-to-End (E2E) para a aplicação ClimateAI usando Playwright. Os testes cobrem:
- ✅ Fluxo de autenticação
- ✅ Navegação entre páginas
- ✅ Componentes UI
- ✅ Performance e carregamento

## 🚀 Como Começar

### 1. Instalação

Playwright já foi instalado como dependência de desenvolvimento:

```bash
cd /home/artha/climateAI/client
npm install @playwright/test
```

### 2. Rodando os Testes

#### Modo padrão (headless)
```bash
npm run test:e2e
```

#### Com interface visual (UI Mode)
```bash
npm run test:e2e:ui
```

#### Com browser visível (headed)
```bash
npm run test:e2e:headed
```

#### Modo debug (interativo)
```bash
npm run test:e2e:debug
```

## 📁 Estrutura dos Testes

```
client/tests/e2e/
├── auth.spec.ts          # Testes de autenticação
├── navigation.spec.ts    # Testes de navegação e rotas
├── components.spec.ts    # Testes de componentes UI
└── performance.spec.ts   # Testes de performance e carregamento
```

### auth.spec.ts
Testa o fluxo completo de autenticação:
- Carregamento da página de boas-vindas
- Navegação para página de login
- Exibição do formulário de autenticação
- Validação de credenciais inválidas
- Validação de formato de email
- Acessibilidade do formulário

**Testes:**
```
✓ should display welcome page on initial load
✓ should navigate to auth page from welcome page
✓ should display login form on auth page
✓ should show error with invalid credentials
✓ should validate email format
✓ should have accessible auth form
```

### navigation.spec.ts
Testa navegação e roteamento da aplicação:
- Navegação entre páginas
- Carregamento de rotas protegidas
- Tratamento de 404
- Persistência de estado
- Códigos de status HTTP

**Testes:**
```
✓ should navigate between pages correctly
✓ should display welcome page
✓ should have navigation menu
✓ should handle protected route access
✓ should handle 404 gracefully
✓ should persist navigation state
✓ should load pages with correct status codes
```

### components.spec.ts
Testa componentes UI e interações:
- Renderização de componentes
- Cliques em botões
- Semântica HTML
- Acessibilidade (labels, aria)
- Responsividade
- Submissão de formulários

**Testes:**
```
✓ should render welcome page components
✓ should handle button clicks
✓ should have accessible headings
✓ should render images with alt text
✓ should have proper color contrast
✓ should handle window resize
✓ should handle form submission
✓ should have proper semantic HTML
```

### performance.spec.ts
Testa performance da aplicação:
- Tempo de carregamento de página
- Lazy loading de páginas
- Cumulative Layout Shift (CLS)
- Console errors
- Tamanho de bundle
- Otimização de imagens
- First Contentful Paint (FCP)

**Testes:**
```
✓ should load page within acceptable time (< 5s)
✓ should handle lazy loading of pages
✓ should render without layout shift
✓ should not have console errors on page load
✓ should lazy load subpages efficiently
✓ should handle images efficiently
✓ should measure First Contentful Paint
```

## 🔧 Configuração

### playwright.config.ts

Arquivo de configuração principal:
- ✅ Testa em 3 navegadores: Chrome, Firefox, Safari
- ✅ Testes responsivos: Desktop, Mobile Chrome, Mobile Safari
- ✅ Inicia servidor dev automaticamente
- ✅ Captura screenshots em caso de falha
- ✅ Gera relatório HTML

### Browsers testados:
- **Desktop Chrome** (1920x1080)
- **Desktop Firefox** (1920x1080)
- **Desktop Safari** (1920x1080)
- **Mobile Chrome** - Pixel 5 (393x851)
- **Mobile Safari** - iPhone 12 (390x844)

## 📊 Relatórios

Após rodar os testes, um relatório HTML é gerado:

```bash
# Abrir relatório em browser
npx playwright show-report
```

O relatório inclui:
- ✅ Resultado de cada teste
- ✅ Screenshots de falhas
- ✅ Traces para debugging
- ✅ Duração de cada teste
- ✅ Navegadores testados

## 🎯 Casos de Uso

### 1. Rodar testes antes de commit
```bash
npm run test:e2e
```

### 2. Rodar testes com interface visual
```bash
npm run test:e2e:ui
```

### 3. Debug de teste específico
```bash
npx playwright test auth.spec.ts --debug
```

### 4. Rodar teste com browser visível
```bash
npx playwright test auth.spec.ts --headed
```

### 5. Gerar trace para análise
```bash
npx playwright test --trace on
```

## 🐛 Troubleshooting

### Port 3000 já em uso
```bash
# Matar processo
lsof -i :3000
kill -9 <PID>
```

### Testes falhando por timeout
Aumentar timeout no playwright.config.ts:
```typescript
use: {
  navigationTimeout: 30000,
  actionTimeout: 10000,
}
```

### Testes não encontrando elementos
- Usar UI mode para debugging interativo: `npm run test:e2e:ui`
- Verificar seletores CSS no browser
- Usar `--debug` flag para parar em breakpoints

## 🚀 CI/CD Integration

Para rodar em CI/CD (GitHub Actions, GitLab CI, etc.):

```yaml
# .github/workflows/test.yml
- name: Run E2E tests
  run: npm run test:e2e
  env:
    CI: true
```

## 📝 Exemplo: Adicionar novo teste

```typescript
test('should do something', async ({ page }) => {
  // Navigate to page
  await page.goto('/some-page');

  // Interact with element
  await page.locator('button').click();

  // Assert outcome
  await expect(page.locator('text=Success')).toBeVisible();
});
```

## ✅ Próximos Passos

1. Rodar testes localmente: `npm run test:e2e`
2. Verificar relatório HTML
3. Integrar testes em CI/CD
4. Adicionar mais testes para funcionalidades específicas
5. Configurar alertas para falhas

## 📚 Referências

- [Playwright Documentation](https://playwright.dev)
- [Playwright Test Guide](https://playwright.dev/docs/intro)
- [API Reference](https://playwright.dev/docs/api/class-test)

---

**Status**: ✅ Testes E2E com Playwright configurados e prontos para uso
**Próxima Etapa**: Etapa 5 - Health Checks Completos
