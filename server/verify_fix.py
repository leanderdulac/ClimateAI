import os
import sys

# Adiciona o diretório atual ao path para simular a execução a partir da raiz do servidor
sys.path.append(os.getcwd())

try:
    print("Tentando importar api.audit...")
    from api.audit import router

    print("SUCESSO: api.audit importado corretamente.")
except ImportError as e:
    print(f"ERRO: Falha ao importar api.audit: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERRO: Erro inesperado: {e}")
    sys.exit(1)

try:
    print("Verificando dependência asyncpg...")
    # Apenas verifica se o nome está nos requisitos, já que não posso instalar no ambiente atual facilmente
    # Mas posso tentar importar se estivesse instalado. Como não sei se está instalado no ambiente do agente,
    # vou verificar se o arquivo requirements.txt contém a linha correta.
    with open("requirements.txt", "r") as f:
        content = f.read()
        if "asyncpg" in content:
            print("SUCESSO: asyncpg encontrado em requirements.txt")
        else:
            print("ERRO: asyncpg NÃO encontrado em requirements.txt")
            sys.exit(1)
except Exception as e:
    print(f"ERRO ao ler requirements.txt: {e}")
    sys.exit(1)
