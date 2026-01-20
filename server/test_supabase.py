#!/usr/bin/env python3
"""
Test script for Supabase integration
Run: python test_supabase.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set credentials if not in env
if not os.getenv("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://tyzmywhvpmdfepxdtyes.supabase.co"
    os.environ["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR5em15d2h2cG1kZmVweGR0eWVzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4NzAzNjcsImV4cCI6MjA4NDQ0NjM2N30.14R4jz5hzgx6u3pPnMDrnBEUmgorb0Iqlb8spQRgzaI"

from config.supabase_client import (
    get_supabase_client,
    is_supabase_configured,
    check_supabase_health,
)


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(test_name: str, success: bool, details: str = ""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {details}")


async def test_connection():
    """Test basic Supabase connection"""
    print_header("Test 1: Connection")
    
    # Check configuration
    configured = is_supabase_configured()
    print_result("Supabase configured", configured)
    
    if not configured:
        print("       Missing SUPABASE_URL or SUPABASE_ANON_KEY")
        return False
    
    # Check health
    health = await check_supabase_health()
    connected = health.get("status") == "connected"
    print_result("Supabase connected", connected, health.get("message", ""))
    
    return connected


async def test_locations_crud():
    """Test CRUD operations on locations table"""
    print_header("Test 2: Locations CRUD")
    
    client = get_supabase_client()
    if not client:
        print_result("Get client", False, "Client is None")
        return False
    
    # CREATE - Insert a test location
    test_location = {
        "name": "Test Farm Location",
        "city": "Ribeirão Preto",
        "state": "SP",
        "country": "Brazil",
        "latitude": -21.1767,
        "longitude": -47.8208,
        "climate_zone": "tropical",
        "risk_zone": "moderate"
    }
    
    try:
        response = client.table("locations").insert(test_location).execute()
        location_id = response.data[0]["id"] if response.data else None
        print_result("CREATE location", bool(location_id), f"ID: {location_id}")
    except Exception as e:
        print_result("CREATE location", False, str(e))
        return False
    
    # READ - Query the location
    try:
        response = client.table("locations").select("*").eq("id", location_id).execute()
        found = len(response.data) > 0
        print_result("READ location", found, f"Found: {response.data[0]['name'] if found else 'N/A'}")
    except Exception as e:
        print_result("READ location", False, str(e))
    
    # UPDATE - Update the location
    try:
        response = client.table("locations").update({"risk_zone": "low"}).eq("id", location_id).execute()
        updated = len(response.data) > 0 and response.data[0]["risk_zone"] == "low"
        print_result("UPDATE location", updated, f"risk_zone -> low")
    except Exception as e:
        print_result("UPDATE location", False, str(e))
    
    # DELETE - Clean up test data
    try:
        client.table("locations").delete().eq("id", location_id).execute()
        print_result("DELETE location", True, "Cleaned up test data")
    except Exception as e:
        print_result("DELETE location", False, str(e))
    
    return True


async def test_policies_table():
    """Test policies table structure"""
    print_header("Test 3: Policies Table")
    
    client = get_supabase_client()
    if not client:
        print_result("Get client", False)
        return False
    
    # First create a location
    try:
        loc_response = client.table("locations").insert({
            "name": "Policy Test Location",
            "city": "São Paulo",
            "state": "SP"
        }).execute()
        location_id = loc_response.data[0]["id"]
        print_result("Create test location", True)
    except Exception as e:
        print_result("Create test location", False, str(e))
        return False
    
    # Create a policy (without user_id since we're not authenticated)
    test_policy = {
        "policy_number": f"POL-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "policy_type": "crop",
        "status": "draft",
        "coverage_amount": 100000.00,
        "premium": 2500.00,
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "expiration_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
        "location_id": location_id,
        "risk_score": 45.5,
        "risk_level": "medium",
        "climate_risk_factor": 0.35
    }
    
    try:
        response = client.table("policies").insert(test_policy).execute()
        policy_id = response.data[0]["id"] if response.data else None
        print_result("CREATE policy", bool(policy_id), f"Policy: {test_policy['policy_number']}")
    except Exception as e:
        print_result("CREATE policy", False, str(e))
        # Clean up location
        client.table("locations").delete().eq("id", location_id).execute()
        return False
    
    # Read policy
    try:
        response = client.table("policies").select("*, locations(name, city)").eq("id", policy_id).execute()
        found = len(response.data) > 0
        print_result("READ policy with relation", found)
    except Exception as e:
        print_result("READ policy with relation", False, str(e))
    
    # Clean up
    try:
        client.table("policies").delete().eq("id", policy_id).execute()
        client.table("locations").delete().eq("id", location_id).execute()
        print_result("CLEANUP", True, "Removed test policy and location")
    except Exception as e:
        print_result("CLEANUP", False, str(e))
    
    return True


async def test_claims_table():
    """Test claims table structure"""
    print_header("Test 4: Claims Table")
    
    client = get_supabase_client()
    if not client:
        return False
    
    # Create location and policy first
    try:
        loc = client.table("locations").insert({"name": "Claims Test", "city": "Curitiba", "state": "PR"}).execute()
        location_id = loc.data[0]["id"]
        
        pol = client.table("policies").insert({
            "policy_number": f"POL-CLAIM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "policy_type": "crop",
            "coverage_amount": 50000,
            "premium": 1500,
            "effective_date": datetime.now().strftime("%Y-%m-%d"),
            "expiration_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "location_id": location_id
        }).execute()
        policy_id = pol.data[0]["id"]
        print_result("Setup policy for claim", True)
    except Exception as e:
        print_result("Setup policy for claim", False, str(e))
        return False
    
    # Create claim
    test_claim = {
        "claim_number": f"CLM-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "policy_id": policy_id,
        "claim_type": "drought",
        "status": "reported",
        "event_date": datetime.now().strftime("%Y-%m-%d"),
        "event_description": "Severe drought affecting 40% of crop area",
        "claimed_amount": 20000.00,
        "damage_percentage": 40.0,
        "weather_data": {"precipitation_mm": 5, "days_without_rain": 45}
    }
    
    try:
        response = client.table("claims").insert(test_claim).execute()
        claim_id = response.data[0]["id"] if response.data else None
        print_result("CREATE claim", bool(claim_id), f"Claim: {test_claim['claim_number']}")
    except Exception as e:
        print_result("CREATE claim", False, str(e))
        # Cleanup
        client.table("policies").delete().eq("id", policy_id).execute()
        client.table("locations").delete().eq("id", location_id).execute()
        return False
    
    # Read claim with policy relation
    try:
        response = client.table("claims").select("*, policies(policy_number, coverage_amount)").eq("id", claim_id).execute()
        found = len(response.data) > 0
        print_result("READ claim with policy", found)
    except Exception as e:
        print_result("READ claim with policy", False, str(e))
    
    # Cleanup
    try:
        client.table("claims").delete().eq("id", claim_id).execute()
        client.table("policies").delete().eq("id", policy_id).execute()
        client.table("locations").delete().eq("id", location_id).execute()
        print_result("CLEANUP", True)
    except Exception as e:
        print_result("CLEANUP", False, str(e))
    
    return True


async def main():
    print("\n" + "="*60)
    print("  SUPABASE INTEGRATION TEST - ClimateAI")
    print("="*60)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Connection", await test_connection()))
    
    if results[0][1]:  # Only continue if connected
        results.append(("Locations CRUD", await test_locations_crud()))
        results.append(("Policies Table", await test_policies_table()))
        results.append(("Claims Table", await test_claims_table()))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! Supabase integration is working correctly.")
    else:
        print("\n  ⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
