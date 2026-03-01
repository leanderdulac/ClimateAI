# Monitoramento e automação do stack ClimateWise

## monitor_stack.sh
Script que monitora continuamente o backend, frontend e landing page:
- Reinicia automaticamente o frontend se a porta 3000 estiver ocupada e o serviço não responder corretamente.
- Reinicia o backend se o health check falhar.
- Reinicia a landing page se necessário.
- Loga todos os eventos em `monitor_stack.log`.

### Uso
```bash
chmod +x monitor_stack.sh
./monitor_stack.sh
```

O script executa em loop infinito, monitorando e reiniciando serviços conforme necessário.

## start_platform.sh / stop_platform.sh / status_platform.sh
Scripts para iniciar, parar e checar status de todos os serviços da plataforma.

- `start_platform.sh`: Inicia backend, frontend e landing page, checando se as portas estão livres.
- `stop_platform.sh`: Para todos os serviços relacionados.
- `status_platform.sh`: Mostra status dos processos e conectividade das portas.

## health_check_backend.py
Script Python que faz health check do backend FastAPI via endpoint `/health`.

### Uso
```bash
.venv/bin/python server/health_check_backend.py
```

Retorna status e código de saída conforme saúde do backend.

---

Para automação total, execute o `monitor_stack.sh` em background ou como serviço do sistema.

Dúvidas ou sugestões, consulte os comentários nos scripts ou README.md.
