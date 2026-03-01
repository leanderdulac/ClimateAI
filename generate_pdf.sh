#!/bin/bash

# Script para gerar PDF da landing page do ClimateWise

echo "🚀 Gerando PDF da Landing Page do ClimateWise..."

# Verificar se o arquivo HTML existe
if [ ! -f "landing-page.html" ]; then
    echo "❌ Erro: Arquivo landing-page.html não encontrado!"
    exit 1
fi

# Gerar PDF usando Chrome headless
google-chrome --headless --disable-gpu \
    --print-to-pdf=landing-page.pdf \
    --no-margins \
    --paper-width=8.27 \
    --paper-height=11.69 \
    file://$(pwd)/landing-page.html 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ PDF gerado com sucesso: $(pwd)/landing-page.pdf"
    echo "📊 Informações do arquivo:"
    ls -lh landing-page.pdf
    echo "📄 Páginas: $(pdfinfo landing-page.pdf 2>/dev/null | grep Pages | awk '{print $2}' || echo 'N/A')"
else
    echo "❌ Erro ao gerar PDF"
    exit 1
fi
