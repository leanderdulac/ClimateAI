#!/usr/bin/env python3
import subprocess
import time
import requests
import signal
import sys
import os

def test_endpoint():
    # Iniciar servidor com uvicorn
    print("Iniciando servidor com uvicorn...")
    env = os.environ.copy()
    env['PATH'] = '/home/artha/climateAI/server/venv/bin:' + env.get('PATH', '')

    server = subprocess.Popen([
        'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--log-level', 'info'
    ], cwd='/home/artha/climateAI/server', env=env)

    try:
        # Esperar servidor iniciar
        time.sleep(6)

        # Testar endpoint
        print("Testando endpoint...")
        response = requests.get(
            'http://localhost:8000/api/v1/clima/previsao?latitude=-23.5505&longitude=-46.6333&dias=7',
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Sucesso! Resposta recebida.")
            print(f"Fonte: {data.get('fonte', 'N/A')}")
            if 'previsao' in data:
                print(f"Número de dias previstos: {len(data['previsao'])}")
                # Mostrar primeira previsão como exemplo
                if data['previsao']:
                    primeira = data['previsao'][0]
                    print(f"Primeira previsão: {primeira.get('data', 'N/A')} - Temp: {primeira.get('temperatura_max', 'N/A')}")
        else:
            print(f"Erro: {response.text}")

    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Parar servidor
        print("Parando servidor...")
        server.terminate()
        server.wait(timeout=5)
        server.kill()

if __name__ == "__main__":
    test_endpoint()
