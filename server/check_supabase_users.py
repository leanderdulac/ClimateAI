#!/usr/bin/env python3
"""
Script para verificar usuários no Supabase.
Requires SUPABASE_URL and SUPABASE_ANON_KEY to be set in environment or .env file.
"""
import asyncio
import os
import sys

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
    print("❌ ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
    sys.exit(1)

from config.supabase_client import get_supabase_client

async def check_supabase_users():
    print('🔍 Verificando usuários no Supabase...')
    print(f'URL: {os.getenv("SUPABASE_URL")}')
    print()

    client = get_supabase_client()
    if not client:
        print('❌ Não foi possível conectar ao Supabase')
        return

    try:
        # Tentar consultar a tabela users (tabela padrão do projeto)
        print('📋 Consultando tabela users...')
        response = client.table('users').select('*').execute()
        users = response.data

        print(f'✅ Total de usuários encontrados: {len(users)}')
        print()

        if users:
            print('👥 Lista de Usuários:')
            print('=' * 60)
            for i, user in enumerate(users, 1):
                # Mostrar todas as chaves disponíveis
                print(f'Usuário {i}:')
                for key, value in user.items():
                    print(f'  {key}: {value}')
                print()
        else:
            print('📭 Nenhum usuário encontrado na tabela users')

            # Tentar outras tabelas possíveis
            print('🔍 Verificando outras tabelas possíveis...')
            tables_to_check = ['user_profiles', 'profiles', 'accounts']

            for table in tables_to_check:
                try:
                    print(f'🔎 Verificando tabela "{table}"...')
                    response = client.table(table).select('*').limit(10).execute()
                    if response.data:
                        print(f'✅ Usuários encontrados na tabela "{table}": {len(response.data)}')
                        print('📋 Dados encontrados:')
                        for user in response.data:
                            print(f'   👤 {user}')
                        print()
                        break
                    else:
                        print(f'📭 Tabela "{table}" está vazia')
                except Exception as e:
                    print(f'❌ Tabela "{table}" não encontrada ou inacessível: {str(e)[:100]}...')

    except Exception as e:
        print(f'❌ Erro ao consultar usuários: {str(e)}')

        # Tentar método alternativo - listar tabelas via REST API
        print('🔄 Tentando método alternativo...')
        try:
            import requests
            url = f"{os.getenv('SUPABASE_URL')}/rest/v1/"
            headers = {
                'apikey': os.getenv('SUPABASE_ANON_KEY'),
                'Authorization': f'Bearer {os.getenv("SUPABASE_ANON_KEY")}'
            }

            # Tentar pegar informações das tabelas
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print('📊 Informações das tabelas disponíveis:')
                print(response.text[:500])
            else:
                print(f'❌ Erro na API REST: {response.status_code}')
        except Exception as rest_e:
            print(f'❌ Erro no método alternativo: {str(rest_e)}')

if __name__ == "__main__":
    asyncio.run(check_supabase_users())