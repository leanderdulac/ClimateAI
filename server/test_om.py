import requests
from datetime import datetime, timedelta

def test_om_date(days_back):
    date_str = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude=-23.9608&longitude=-46.3336&start_date={date_str}&end_date={date_str}&daily=precipitation_sum&timezone=America%2FSao_Paulo"
    res = requests.get(url)
    print(f"Days back: {days_back}, Date: {date_str}, Status: {res.status_code}")
    if res.status_code != 200:
        print(res.json())

for i in range(10):
    test_om_date(i)
