import functions_framework
import json
import os
import logging
from services.gee_service import GoogleEarthEngineService
from services.tokenization_service import TokenizationService

logger = logging.getLogger(__name__)

@functions_framework.http
def oracle_payout_trigger(request):
    """
    Cloud Function Oracle:
    1. Fetches NDVI from Google Earth Engine.
    2. If Severity Score meets threshold (Score >= 3), triggers on-chain mint/payout.
    3. Transaction is signed via KMS HSM.
    """
    request_json = request.get_json(silent=True)
    
    # Required params
    lat = request_json.get('latitude')
    lon = request_json.get('longitude')
    dest_address = request_json.get('destination_address')
    
    if not all([lat, lon, dest_address]):
        return json.dumps({"error": "Missing parameters"}), 400

    try:
        # 1. Fetch satellite intelligence
        gee = GoogleEarthEngineService()
        import asyncio
        # Cloud Functions are usually synchronous, we run the async loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        satellite_data = loop.run_until_complete(
            gee.get_satellite_metrics(lat, lon, datetime.now(), datetime.now())
        )
        
        # 2. Heuristic Scoring (Oracle Logic)
        ndvi = satellite_data.get('ndvi', 0.5)
        severity_score = (0.6 - ndvi) * 10 # Simple inverse relationship for drought
        
        if severity_score >= 3.0:
            # 3. Trigger Blockchain Action signed by KMS
            ts = TokenizationService()
            
            # ERC-3525 Logic:
            # Slot based on region/severity category
            slot = 100 # Default drought slot
            # Value based on severity (Sum Insured)
            value = int(severity_score * 1000)
            
            logger.info(f"Oracle triggering ERC-3525 Mint: Slot {slot}, Value {value}")
            receipt = ts.mint_policy(dest_address, slot, value)
            
            return json.dumps({
                "status": "PAYOUT_TRIGGERED",
                "severity_score": severity_score,
                "token_value": value,
                "tx_hash": receipt.get('transactionHash').hex() if receipt else "mock",
                "address": dest_address
            }), 200
        else:
            return json.dumps({
                "status": "NO_PAYOUT",
                "severity": severity_score,
                "reason": "Threshold not met"
            }), 200

    except Exception as e:
        logger.error(f"Oracle Failure: {e}")
        return json.dumps({"error": str(e)}), 500
