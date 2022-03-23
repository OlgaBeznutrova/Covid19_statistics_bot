import requests

from cachetools import TTLCache, cached


class CountryService:
    """This class provides country information"""

    # class constructor
    def __init__(self, geo_api_key, covid_api_token):
        try:
            self.geo_api_key = geo_api_key
            self.covid_api_token = covid_api_token
        except Exception as e:
            raise e

    # 3 hours cache time
    cache = TTLCache(maxsize=100, ttl=10800)

    # method for getting country information by latitude and longitude
    @cached(cache)
    def get_country_information_by_lat_lng(self, latitude, longitude):
        url = "http://api.geonames.org/countrySubdivisionJSON"
        params = {
            "lat": latitude,
            "lng": longitude,
            "username": self.geo_api_key
        }
        geo_result = requests.get(url=url, params=params)
        return geo_result.json()

    # method for getting countries by part_of_name or the name
    def get_countries_by_part_of_name(self, part_of_name):
        url = "https://covid-193.p.rapidapi.com/countries"
        params = {"search": part_of_name}
        headers = {
            "x-rapidapi-host": "covid-193.p.rapidapi.com",
            "x-rapidapi-key": self.covid_api_token
        }
        found_countries = requests.get(url=url, params=params, headers=headers)
        return found_countries.json()
