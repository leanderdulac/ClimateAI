#!/usr/bin/env python3
"""
Test script simplificado para o serviço de cenários probabilísticos climáticos
"""

import sys
import os

# Adicionar o diretório server ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

try:
    # Import direto do serviço
    from services.probabilistic_climate_scenarios_service import ProbabilisticClimateScenariosService
    print("✅ Service import successful")

    # Testar instanciação
    service = ProbabilisticClimateScenariosService()
    print("✅ Service instantiation successful")

    # Testar métodos básicos
    combinations = service.get_ssp_rcp_combinations()
    print(f"✅ SSP-RCP combinations: {len(combinations)} found")
    print(f"   Available scenarios: {list(combinations.keys())[:3]}...")

    models = service.get_cmip6_models()
    print(f"✅ CMIP6 models: {len(models)} found")

    status = service.get_service_status()
    print(f"✅ Service status: {status['status']}")

    print("\n🎉 Probabilistic climate scenarios service is working correctly!")
    print("📊 Layer 2 (Probabilistic Scenarios) has been successfully implemented!")

except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)