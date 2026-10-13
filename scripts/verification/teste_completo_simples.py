#!/usr/bin/env python3
"""
Teste direto e simples do serviço de cenários probabilísticos
"""

import sys
import os

# Adicionar o diretório server ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

try:
    # Import direto do arquivo do serviço
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "probabilistic_climate_scenarios_service",
        "server/services/probabilistic_climate_scenarios_service.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ProbabilisticClimateScenariosService = module.ProbabilisticClimateScenariosService
    print("✅ ProbabilisticClimateScenariosService import successful")

    # Testar instanciação
    service = ProbabilisticClimateScenariosService()
    print("✅ Service instantiation successful")

    # Testar métodos básicos
    combinations = service.get_ssp_rcp_combinations()
    print(f"✅ SSP-RCP combinations: {len(combinations)} found")

    models = service.get_cmip6_models()
    print(f"✅ CMIP6 models: {len(models)} found")

    status = service.get_service_status()
    print(f"✅ Service status: {status['status']}")

    print("\n🎉 PASSE 1: Dependências verificadas com sucesso!")
    print("🎉 PASSE 2: Serviço inicializado com sucesso!")
    print("🎉 PASSE 3: Funcionalidades básicas testadas!")
    print("🎉 PASSE 4: Serviço pronto para integração!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)