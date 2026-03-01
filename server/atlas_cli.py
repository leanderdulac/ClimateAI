#!/usr/bin/env python3
"""
Script utilitário para o módulo Atlas Digital de Desastres

Uso:
    python atlas_cli.py --help
    python atlas_cli.py download --url "https://..."
    python atlas_cli.py filter --uf RS --tipo inundacao
    python atlas_cli.py stats
    python atlas_cli.py visualize --all
"""

import argparse
import json
import sys
import os
from datetime import datetime

# Adicionar server ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
except ImportError:
    print("Erro: requests não instalado. Execute: pip install requests")
    sys.exit(1)


class AtlasCLI:
    """Interface de linha de comando para o módulo Atlas"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1/atlas"

    def check_server(self) -> bool:
        """Verificar se o servidor está disponível"""
        try:
            response = requests.get(f"{self.api_base}/status", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def download(self, url: str, filename: str = None, force: bool = False):
        """Fazer download de dados do Atlas"""
        payload = {"url": url, "force": force}
        if filename:
            payload["filename"] = filename

        print(f"Baixando dados de: {url}")
        response = requests.post(f"{self.api_base}/download", json=payload)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Download realizado: {data['filepath']}")
            return data
        else:
            print(f"✗ Erro: {response.json()}")
            return None

    def status(self):
        """Verificar status dos dados"""
        response = requests.get(f"{self.api_base}/status")
        if response.status_code == 200:
            data = response.json()
            print("\n=== Status dos Dados ===")
            print(f"Arquivo: {data.get('arquivo_carregado', 'Nenhum')}")
            print(f"Registros: {data.get('total_registros', 0):,}")
            print(f"Cache: {data.get('cache_timestamp', 'N/A')}")
            print(f"Diretório: {data.get('data_dir', 'N/A')}")
            return data
        return None

    def filter(
        self,
        anos: str = None,
        uf: str = None,
        tipo: str = None,
        municipio: str = None,
        min_afetados: int = None,
        output: str = None,
    ):
        """Filtrar dados do Atlas"""
        payload = {}

        if anos:
            try:
                parts = anos.split("-")
                if len(parts) == 2:
                    payload["anos"] = [int(parts[0]), int(parts[1])]
            except ValueError:
                print(f"Erro: Formato de ano inválido. Use: 2000-2024")
                return

        if uf:
            payload["uf"] = uf.upper()
        if tipo:
            payload["tipo_desastre"] = tipo
        if municipio:
            payload["municipio"] = municipio
        if min_afetados:
            payload["min_afetados"] = min_afetados

        print(f"Filtrando dados... {payload}")
        response = requests.post(f"{self.api_base}/filter", json=payload)

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Filtro aplicado: {data['total']} registros encontrados")

            if output:
                # Salvar resultados
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(data["data"], f, indent=2, ensure_ascii=False)
                print(f"✓ Dados salvos em: {output}")
            else:
                # Mostrar resumo
                print(f"\nPrimeiros 5 registros:")
                for i, reg in enumerate(data["data"][:5], 1):
                    print(f"  {i}. {reg.get('municipio', 'N/A')}/{reg.get('uf', 'N/A')} - {reg.get('tipo_desastre', 'N/A')}")

            return data
        else:
            print(f"✗ Erro: {response.json()}")
            return None

    def statistics(self):
        """Obter estatísticas"""
        response = requests.get(f"{self.api_base}/statistics")

        if response.status_code == 200:
            data = response.json()
            print("\n=== Estatísticas ===")
            print(f"Total de registros: {data.get('total_registros', 0):,}")

            periodo = data.get("periodo", {})
            print(f"Período: {periodo.get('inicio', 'N/A')} - {periodo.get('fim', 'N/A')}")

            tipos = data.get("tipos_desastre", {})
            print(f"Tipo mais comum: {tipos.get('mais_comum', 'N/A')}")

            impacto = data.get("impacto", {})
            if "mortes_diretas" in impacto:
                mortes = impacto["mortes_diretas"]
                print(f"Total de mortes: {mortes.get('total', 0):,}")

            if "afetados" in impacto:
                afetados = impacto["afetados"]
                print(f"Total de afetados: {afetados.get('total', 0):,}")

            return data
        return None

    def top_affected(self, limit: int = 10, metric: str = "qtd_ocorrencias"):
        """Obter municípios mais afetados"""
        response = requests.get(
            f"{self.api_base}/analysis/top-affected",
            params={"limit": limit, "metric": metric}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n=== Top {limit} Municípios ({metric}) ===")
            for i, item in enumerate(data, 1):
                municipio = item.get("municipio", "N/A")
                uf = item.get("uf", "N/A")
                valor = item.get(metric, 0)
                print(f"{i:2}. {municipio}/{uf}: {valor:,}")
            return data
        return None

    def trends(self):
        """Obter tendências temporais"""
        response = requests.get(f"{self.api_base}/analysis/trends")

        if response.status_code == 200:
            data = response.json()
            print("\n=== Tendências Temporais ===")

            stats = data.get("estatisticas", {})
            print(f"Média anual: {stats.get('media_anual', 0):,.0f}")
            print(f"Ano com mais ocorrências: {stats.get('ano_max', 'N/A')}")
            print(f"Ano com menos ocorrências: {stats.get('ano_min', 'N/A')}")

            return data
        return None

    def visualize(self, chart_type: str = None, output_dir: str = None):
        """Gerar visualizações"""
        if chart_type == "all" or chart_type is None:
            # Gerar todas as visualizações
            print("Gerando todas as visualizações...")
            response = requests.post(
                f"{self.api_base}/visualizations/generate-all",
                json={"prefix": "atlas"}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ Visualizações geradas: {data['total_generated']}")
                for name, path in data.get("visualizations", {}).items():
                    print(f"  - {name}: {path}")
                return data
        else:
            # Gerar visualização específica
            endpoints = {
                "timeseries": "/visualizations/timeseries",
                "map": "/visualizations/map",
                "pie": "/visualizations/pie-chart",
                "impact": "/visualizations/impact-analysis",
            }

            if chart_type not in endpoints:
                print(f"Erro: Tipo '{chart_type}' não suportado")
                print(f"Tipos válidos: {list(endpoints.keys())}")
                return

            print(f"Gerando {chart_type}...")
            response = requests.get(
                f"{self.api_base}{endpoints[chart_type]}",
                params={"return_base64": False}
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✓ Visualização gerada: {data.get('data', 'N/A')}")
                return data

        print("✗ Erro ao gerar visualização")
        return None

    def export(self, filename: str, filters: dict = None):
        """Exportar dados para CSV"""
        payload = {"filename": filename}
        if filters:
            # Aplicar filtros na exportação
            filter_response = requests.post(
                f"{self.api_base}/filter",
                json=filters
            )
            if filter_response.status_code != 200:
                print(f"Erro no filtro: {filter_response.json()}")
                return

        print(f"Exportando para: {filename}")
        response = requests.post(f"{self.api_base}/export/csv", json=payload)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Exportado: {data['filepath']} ({data['total_registros']:,} registros)")
            return data
        else:
            print(f"✗ Erro: {response.json()}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description="CLI para o módulo Atlas Digital de Desastres",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s status
  %(prog)s download --url "https://exemplo.com/dados.csv"
  %(prog)s filter --uf RS --tipo inundacao --anos 2000-2024
  %(prog)s stats
  %(prog)s top --limit 20
  %(prog)s trends
  %(prog)s visualize --all
  %(prog)s export --file dados_filtrados.csv --uf RS
        """
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="URL base do servidor (padrão: http://localhost:8000)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comando")

    # Status
    subparsers.add_parser("status", help="Verificar status dos dados")

    # Download
    p_download = subparsers.add_parser("download", help="Download de dados")
    p_download.add_argument("--url", required=True, help="URL do arquivo CSV/Excel")
    p_download.add_argument("--filename", help="Nome do arquivo")
    p_download.add_argument("--force", action="store_true", help="Forçar download")

    # Filter
    p_filter = subparsers.add_parser("filter", help="Filtrar dados")
    p_filter.add_argument("--anos", help="Intervalo de anos (ex: 2000-2024)")
    p_filter.add_argument("--uf", help="Sigla da UF (ex: RS)")
    p_filter.add_argument("--tipo", help="Tipo de desastre (ex: inundacao)")
    p_filter.add_argument("--municipio", help="Nome do município")
    p_filter.add_argument("--min-afetados", type=int, help="Mínimo de afetados")
    p_filter.add_argument("--output", "-o", help="Arquivo de saída (JSON)")

    # Statistics
    subparsers.add_parser("stats", help="Estatísticas descritivas")

    # Top affected
    p_top = subparsers.add_parser("top", help="Municípios mais afetados")
    p_top.add_argument("--limit", type=int, default=10, help="Número de municípios")
    p_top.add_argument(
        "--metric",
        default="qtd_ocorrencias",
        choices=["qtd_ocorrencias", "total_afetados", "total_mortes"],
        help="Métrica para ranking"
    )

    # Trends
    subparsers.add_parser("trends", help="Tendências temporais")

    # Visualize
    p_viz = subparsers.add_parser("visualize", help="Gerar visualizações")
    p_viz.add_argument(
        "--type",
        choices=["timeseries", "map", "pie", "impact", "all"],
        help="Tipo de visualização"
    )

    # Export
    p_export = subparsers.add_parser("export", help="Exportar para CSV")
    p_export.add_argument("--file", required=True, help="Nome do arquivo CSV")
    p_export.add_argument("--uf", help="Filtrar por UF")
    p_export.add_argument("--tipo", help="Filtrar por tipo")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Criar CLI
    cli = AtlasCLI(base_url=args.url)

    # Verificar servidor
    if not cli.check_server():
        print(f"Erro: Não foi possível conectar ao servidor em {args.url}")
        print("Verifique se o servidor está rodando:")
        print("  cd server && uvicorn main:app --reload")
        sys.exit(1)

    # Executar comando
    if args.command == "status":
        cli.status()

    elif args.command == "download":
        cli.download(url=args.url, filename=args.filename, force=args.force)

    elif args.command == "filter":
        cli.filter(
            anos=args.anos,
            uf=args.uf,
            tipo=args.tipo,
            municipio=args.municipio,
            min_afetados=args.min_afetados,
            output=args.output
        )

    elif args.command == "stats":
        cli.statistics()

    elif args.command == "top":
        cli.top_affected(limit=args.limit, metric=args.metric)

    elif args.command == "trends":
        cli.trends()

    elif args.command == "visualize":
        cli.visualize(chart_type=args.type)

    elif args.command == "export":
        filters = {}
        if args.uf:
            filters["uf"] = args.uf
        if args.tipo:
            filters["tipo_desastre"] = args.tipo

        cli.export(filename=args.file, filters=filters if filters else None)


if __name__ == "__main__":
    main()
