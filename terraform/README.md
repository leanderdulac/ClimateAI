# ClimateWise Infrastructure as Code (IaC) - Terraform

## 📊 Visão Geral

Este diretório contém a configuração Terraform para deploy da plataforma ClimateWise em múltiplos ambientes.

## 🏗️ Estrutura

```
terraform/
├── modules/
│   ├── database/          # PostgreSQL + Redis
│   ├── compute/           # Containers/VMs
│   ├── networking/        # VPC, Subnets, Load Balancer
│   └── monitoring/        # Prometheus, Grafana, Alertas
├── environments/
│   ├── dev/              # Ambiente de desenvolvimento
│   └── prod/             # Ambiente de produção
└── scripts/
    ├── init.sh           # Inicialização
    ├── plan.sh           # Preview de mudanças
    └── apply.sh          # Aplicar mudanças
```

## 🚀 Quick Start

### 1. Inicializar
```bash
cd terraform/environments/dev
terraform init
```

### 2. Planejar
```bash
terraform plan -out=tfplan
```

### 3. Aplicar
```bash
terraform apply tfplan
```

### 4. Destruir (apenas dev)
```bash
terraform destroy
```

## 📋 Módulos Disponíveis

| Módulo | Descrição | Recursos |
|--------|-----------|----------|
| **database** | Banco de dados e cache | PostgreSQL, Redis, Backups |
| **compute** | Computação | Docker, Kubernetes, ou VMs |
| **networking** | Rede | VPC, Subnets, LB, Firewall |
| **monitoring** | Monitoramento | Prometheus, Grafana, Alertas |

## 🔐 Variáveis de Ambiente

```bash
# Required
export TF_VAR_project_name="climatewise"
export TF_VAR_environment="dev"
export TF_VAR_region="us-east-1"

# Optional
export TF_VAR_enable_monitoring="true"
export TF_VAR_enable_backups="true"
```

## 📚 Documentação

- [Módulo Database](modules/database/README.md)
- [Módulo Compute](modules/compute/README.md)
- [Módulo Networking](modules/networking/README.md)
- [Módulo Monitoring](modules/monitoring/README.md)

## 🧪 Testes

```bash
# Testar configuração
terraform validate

# Formatar
terraform fmt -recursive

# Security scan
terraform scan  # Requer checkov ou tfsec
```

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
- name: Setup Terraform
  uses: hashicorp/setup-terraform@v2

- name: Terraform Init
  run: terraform init

- name: Terraform Plan
  run: terraform plan -out=tfplan

- name: Terraform Apply
  run: terraform apply -auto-approve tfplan
```

## 📞 Suporte

Para issues relacionados à infraestrutura, abra um ticket no GitHub.
