# 🔐 Credenciais de Teste - ClimateWise

## ✅ Login com Dados Mock (Habilitado)

Para testes e desenvolvimento, o modo **MOCK DATA** está habilitado.

### Credenciais de Teste

Use **qualquer** email e senha com comprimento mínimo:

```
Email: teste@climatewise.com
Senha: teste123
```

Ou qualquer combinação de email/senha (mínimo 6 caracteres).

### Como Funciona

O modo mock simula autenticação sem precisar de:
- ✅ Confirmação de email
- ✅ Banco de dados de usuários
- ✅ Validação de senha real

### Arquivo de Configuração

```bash
# client/.env
VITE_USE_MOCK_DATA=true
```

---

## 📝 Login Real com Supabase (Produção)

Para usar autenticação real:

1. **Desabilitar modo mock**:
   ```bash
   # client/.env
   VITE_USE_MOCK_DATA=false
   ```

2. **Criar usuário no Supabase**:
   ```bash
   cd server
   python3 create_test_user.py
   ```

3. **Confirmar email** (se necessário):
   - Acesse o email enviado pelo Supabase
   - Ou use a API admin para confirmar

4. **Fazer login**:
   - Use as credenciais criadas

---

## 🚀 Status Atual

| Modo | Status | Email | Senha |
|------|--------|-------|-------|
| **Mock** | ✅ Habilitado | teste@climatewise.com | teste123 |
| **Supabase Real** | ⚠ Requer confirmação | - | - |

---

## 🔧 Troubleshooting

### "Email not confirmed"
- Use o modo mock para testes
- Ou confirme o email no Supabase

### "Invalid credentials"
- Verifique email e senha
- No modo mock, use mínimo 6 caracteres

### "Supabase not configured"
- Verifique `VITE_SUPABASE_URL` e `VITE_SUPABASE_ANON_KEY` no `.env`

---

*Atualizado: 18 de Fevereiro de 2026*
