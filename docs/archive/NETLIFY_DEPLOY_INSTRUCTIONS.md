# Instruções para Deploy no Netlify

## 🎯 Status Atual

**Commits realizados:**
- ✅ `e5fefa2`: Remover `tsc -b` e ajustar TypeScript config
- ✅ `6496e65`: Corrigir Vite alias com `path.resolve`
- ✅ `8234aff`: Usar alias `@` em main.tsx
- ✅ `67ac75b`: Simplificar import em vite.config.ts

**Build local:** ✅ Testado e funcionando (57.15s)

## 🔄 Próximos Passos no Netlify

### Opção 1: Redeploy com Clear Cache (Recomendado)

1. Acesse o dashboard do Netlify
2. Vá em **Deploys** → **Trigger Deploy**
3. Selecione **"Clear cache and deploy site"**
4. Aguarde o build completar

### Opção 2: Forçar Novo Build

Se o Netlify ainda mostrar cache antigo:

1. No dashboard Netlify, vá em **Site Settings**
2. Vá em **Build & deploy** → **Environment**
3. Adicione variável temporária:
   - Key: `NETLIFY_CLEAR_CACHE`
   - Value: `true`
4. Faça um novo deploy (automaticamente ou manual)
5. Após sucesso, remova a variável

### Opção 3: Git Force Push (Último Recurso)

```bash
cd /home/artha/climateAI
git commit --allow-empty -m "chore: Forçar redeploy Netlify"
git push origin main
```

## 📋 Verificações Pós-Deploy

Após o deploy bem-sucedido, verifique:

1. **Build Logs**
   - ✅ "vite build" deve completar sem erros
   - ✅ Não deve aparecer "Could not resolve"
   - ✅ Deve gerar arquivos em dist/

2. **Site Publicado**
   - ✅ Acessar URL do Netlify
   - ✅ Página deve carregar (não ficar branca)
   - ✅ Navegação entre rotas deve funcionar
   - ✅ Console do navegador sem erros críticos

3. **Redirects SPA**
   - ✅ Acessar rota direta (ex: `/dashboard`)
   - ✅ Deve carregar, não dar 404
   - ✅ Reload em qualquer rota deve funcionar

## 🔍 Troubleshooting

### Se ainda aparecer "Could not resolve ./lib/error-handler"

Isso indica que o Netlify está usando cache antigo. Soluções:

1. **Clear cache** (ver Opção 1 acima)
2. Verificar se commit mais recente está no GitHub:
   ```bash
   git log --oneline -1
   # Deve mostrar: 67ac75b refactor: Simplificar import...
   ```
3. No Netlify, verificar qual commit está sendo deployado
   - Deve ser `67ac75b` ou posterior

### Se aparecerem outros erros

1. **Module not found**: Verificar se arquivo existe em `client/src/lib/`
2. **TypeScript errors**: Verificar `tsconfig.app.json` (strict=false)
3. **Build timeout**: Aumentar timeout no Netlify settings

## 📝 Configuração Atual

### netlify.toml
```toml
[build]
  publish = "client/dist"
  command = "cd client && npm install && npm run build"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### vite.config.ts
```typescript
import { resolve } from 'path'

resolve: {
  alias: {
    "@": resolve(__dirname, 'src'),
  },
}
```

### package.json
```json
"build": "vite build"
```

## ✅ Checklist de Deploy

- [x] Código commitado no GitHub
- [x] Build testado localmente
- [x] Imports usando alias `@`
- [x] netlify.toml configurado
- [x] TypeScript config ajustado
- [ ] Clear cache no Netlify
- [ ] Deploy executado
- [ ] Site verificado online

---

**Última atualização:** 14 de outubro de 2025
**Status:** Aguardando clear cache e redeploy no Netlify
