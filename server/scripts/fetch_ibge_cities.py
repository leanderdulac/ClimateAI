import json
import os
from pathlib import Path

import requests

# URL da API do IBGE para municípios
IBGE_API_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


def fetch_cities():
    print("Fetching cities from IBGE API...")
    try:
        response = requests.get(IBGE_API_URL)
        response.raise_for_status()
        cities_data = response.json()

        formatted_cities = []

        for city in cities_data:
            # Extrair dados relevantes
            name = city["nome"]
            state_sigla = city["microrregiao"]["mesorregiao"]["UF"]["sigla"]
            state_name = city["microrregiao"]["mesorregiao"]["UF"]["nome"]

            # A API de municípios não retorna lat/long diretamente.
            # Precisamos de outra estratégia ou assumir que o geocoding fará o trabalho pesado depois.
            # MAS, para o br_cities.json funcionar como cache/lookup rápido, lat/long é bom.
            # Vamos tentar pegar lat/long de outra fonte ou usar o geocoding service para popular aos poucos?
            # O br_cities.json atual TEM lat/long.

            # Alternativa: Usar uma lista estática mais completa ou uma API que retorne tudo.
            # A API do IBGE tem um endpoint de distritos que pode ter mais info, ou podemos usar o BrasilAPI.
            # Vamos tentar BrasilAPI que costuma ser mais amigável para devs.
            pass

        return cities_data

    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def fetch_cities_brasilapi():
    """
    Tenta buscar do BrasilAPI que já fornece coordenadas (se disponível) ou
    pelo menos uma lista mais limpa.

    Na verdade, a melhor fonte com coordenadas para TODAS as cidades é o IBGE + processamento,
    ou um arquivo estático pronto.

    Vou usar uma abordagem híbrida:
    1. Baixar lista do IBGE.
    2. Para coordenadas, o dataset atual é muito pequeno.

    Se eu não tiver coordenadas, o frontend/mapa pode quebrar se depender disso para plotar.
    O `geocoding_service` usa `Nominatim` para buscar se não achar no cache.

    Então, se eu popular o `br_cities.json` apenas com nomes e estados, o `geocoding_service`
    vai tentar buscar no Nominatim na primeira vez que for usado.

    Mas o `search_cities` retorna o que está no JSON. Se o JSON não tiver lat/long,
    o frontend pode reclamar se esperar esses campos.

    Vamos verificar o `br_cities.json` atual. Ele tem lat/long.

    Vou usar uma biblioteca python `geopy` ou similar para tentar obter coordenadas em batch? Demora muito.

    Melhor solução agora:
    Baixar a lista do IBGE.
    Manter lat/long como None ou 0.0 se não tiver.
    O `geocoding_service` deve ser robusto o suficiente para buscar lat/long on-demand se faltar,
    OU o frontend deve lidar com isso.

    Olhando o `geocoding_service.py`:
    `search_cities` retorna o entry direto.

    Se eu entregar sem lat/long, o usuário clica, e o frontend provavelmente chama algum endpoint para pegar detalhes?
    Não, o frontend costuma usar o objeto retornado.

    Vou procurar um JSON pronto com lat/long das cidades brasileiras no GitHub raw content.
    Existem vários gists com isso.

    Vou tentar o endpoint: https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/json/municipios.json
    Esse repo é famoso.
    """
    print("Fetching cities from GitHub (kelvins/municipios-brasileiros)...")
    url = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/json/municipios.json"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # O formato desse JSON é:
        # {
        #   "codigo_ibge": 5200050,
        #   "nome": "Abadia de Goiás",
        #   "latitude": -16.7573,
        #   "longitude": -49.4412,
        #   "capital": 0,
        #   "codigo_uf": 52
        # }

        # Precisamos mapear código UF para Sigla UF.
        uf_map = {
            11: "RO",
            12: "AC",
            13: "AM",
            14: "RR",
            15: "PA",
            16: "AP",
            17: "TO",
            21: "MA",
            22: "PI",
            23: "CE",
            24: "RN",
            25: "PB",
            26: "PE",
            27: "AL",
            28: "SE",
            29: "BA",
            31: "MG",
            32: "ES",
            33: "RJ",
            35: "SP",
            41: "PR",
            42: "SC",
            43: "RS",
            50: "MS",
            51: "MT",
            52: "GO",
            53: "DF",
        }

        uf_names = {
            "RO": "Rondônia",
            "AC": "Acre",
            "AM": "Amazonas",
            "RR": "Roraima",
            "PA": "Pará",
            "AP": "Amapá",
            "TO": "Tocantins",
            "MA": "Maranhão",
            "PI": "Piauí",
            "CE": "Ceará",
            "RN": "Rio Grande do Norte",
            "PB": "Paraíba",
            "PE": "Pernambuco",
            "AL": "Alagoas",
            "SE": "Sergipe",
            "BA": "Bahia",
            "MG": "Minas Gerais",
            "ES": "Espírito Santo",
            "RJ": "Rio de Janeiro",
            "SP": "São Paulo",
            "PR": "Paraná",
            "SC": "Santa Catarina",
            "RS": "Rio Grande do Sul",
            "MS": "Mato Grosso do Sul",
            "MT": "Mato Grosso",
            "GO": "Goiás",
            "DF": "Distrito Federal",
        }

        formatted_cities = []
        for item in data:
            uf_code = item.get("codigo_uf")
            state_sigla = uf_map.get(uf_code)

            if not state_sigla:
                continue

            formatted_cities.append(
                {
                    "city": item["nome"],
                    "state": state_sigla,
                    "state_name": uf_names.get(state_sigla, ""),
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "country": "Brasil",
                }
            )

        return formatted_cities

    except Exception as e:
        print(f"Error fetching from GitHub: {e}")
        return []


def main():
    cities = fetch_cities_brasilapi()

    if not cities:
        print("No cities found. Aborting.")
        return

    output_path = Path(__file__).resolve().parents[1] / "data" / "br_cities.json"

    # Backup existing file
    if output_path.exists():
        backup_path = output_path.with_suffix(".json.bak")
        print(f"Backing up existing file to {backup_path}")
        output_path.rename(backup_path)

    print(f"Saving {len(cities)} cities to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cities, f, ensure_ascii=False, indent=2)

    print("Done!")


if __name__ == "__main__":
    main()
