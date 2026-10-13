"""
Locust Performance and Load Testing Suite for ClimateWise
Simulates concurrent actuarial, climate forecast, and pricing queries.
"""

import json
import logging
from locust import HttpUser, between, task

logger = logging.getLogger("locust")


class ClimateWiseUser(HttpUser):
    wait_time = between(0.5, 2.0)
    token: str = ""
    headers: dict = {}

    def on_start(self):
        """Authenticate user on start to test protected endpoints."""
        login_payload = {
            "email": "loadtest@climatewise.ai",
            "password": "LoadTestSecurePassword123!",
        }
        # Try login or register
        resp = self.client.post("/api/v1/auth/login", json=login_payload)
        if resp.status_code == 401 or resp.status_code == 404:
            reg = self.client.post(
                "/api/v1/auth/register",
                json={
                    "email": "loadtest@climatewise.ai",
                    "password": "LoadTestSecurePassword123!",
                    "full_name": "Load Test Runner",
                },
            )
            if reg.status_code in (200, 201):
                resp = self.client.post("/api/v1/auth/login", json=login_payload)

        if resp.status_code == 200:
            token = resp.json().get("access_token")
            if token:
                self.token = token
                self.headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }

    @task(5)
    def test_health_endpoint(self):
        """High-frequency health check ping."""
        self.client.get("/health", name="/health")

    @task(3)
    def test_climate_forecast(self):
        """Test weather forecast calculation endpoint."""
        params = {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "dias": 7,
        }
        self.client.get("/api/v1/clima/previsao", params=params, headers=self.headers, name="/api/v1/clima/previsao")

    @task(2)
    def test_actuarial_quote(self):
        """Simulate parametric insurance actuarial quote calculation."""
        payload = {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "coverage_amount": 100000.0,
            "trigger_type": "drought",
            "strike_value": 35.0,
        }
        self.client.post("/api/v1/pricing/quote", json=payload, headers=self.headers, name="/api/v1/pricing/quote")

    @task(2)
    def test_climate_events(self):
        """Test active extreme event queries."""
        params = {"latitude": -23.5505, "longitude": -46.6333, "raio": 50}
        self.client.get("/api/v1/eventos", params=params, headers=self.headers, name="/api/v1/eventos")
