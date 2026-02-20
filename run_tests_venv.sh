#!/bin/bash
# Ativa o ambiente virtual e executa os testes Python

if [ -d ".venv" ]; then
  source .venv/bin/activate
else
  echo "Ambiente virtual .venv não encontrado!"
  exit 1
fi

pytest --maxfail=5 --disable-warnings
