import json
import time

from locust import HttpUser, between, task
from locust_plugins.csvreader import CSVReader

# CSV reader for test data
cities_reader = CSVReader("data/br_cities.json")


class ClimateWiseUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login and get access token on start"""
        response = self.client.post(
            "/api/auth/login",
            json={"username": "test_user", "password": "test_password"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def get_weather_data(self):
        """Test weather data endpoint"""
        if hasattr(self, "token") and self.token:
            # Get a random city for testing
            try:
                with open("data/br_cities.json", "r") as f:
                    cities = json.load(f)
                    if cities:
                        city = cities[0]  # Use first city for simplicity
                        self.client.get(
                            f"/api/clima/weather?lat={city['lat']}&lon={city['lon']}",
                            headers=self.headers,
                        )
            except:
                pass

    @task(2)
    def get_climate_forecast(self):
        """Test climate forecast endpoint"""
        if hasattr(self, "token") and self.token:
            try:
                with open("data/br_cities.json", "r") as f:
                    cities = json.load(f)
                    if cities:
                        city = cities[0]
                        self.client.get(
                            f"/api/previsao/forecast?lat={city['lat']}&lon={city['lon']}&days=7",
                            headers=self.headers,
                        )
            except:
                pass

    @task(1)
    def get_alerts(self):
        """Test alerts endpoint"""
        if hasattr(self, "token") and self.token:
            self.client.get("/api/alertas/active", headers=self.headers)

    @task(1)
    def get_audit_logs(self):
        """Test audit endpoint"""
        if hasattr(self, "token") and self.token:
            self.client.get("/api/audit/logs?page=1&limit=10", headers=self.headers)
