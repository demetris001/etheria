import requests
from django.conf import settings

def search_flights(origin, destination, departure_date, return_date=None):
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    params = {
        'origin': origin,
        'destination': destination,
        'departure_at': departure_date,
        'return_at': return_date,
        'unique': 'false',
        'sorting': 'price',
        'direct': 'false',
        'currency': 'eur',
        'limit': 10,
        'page': 1,
        'one_way': 'true' if not return_date else 'false',
        'token': settings.TRAVELPAYOUTS_API_KEY,
    }
    # Αφαίρεσε κενά params
    params = {k: v for k, v in params.items() if v is not None}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None
