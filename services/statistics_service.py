import requests
import ciso8601

from jinja2 import Template
from cachetools import TTLCache, cached


class StatisticsService:
    """This class provides Covid19 stats"""

    # cache time 3 hours
    cache = TTLCache(maxsize=100, ttl=10800)

    def __init__(self, covid_api_token, db_context, country_service):
        try:
            self.covid_api_token = covid_api_token
            self.db_context = db_context
            self.country_service = country_service
        except Exception as e:
            raise e

    # method for getting statistics from API
    def __get_statistics_by_country_from_api(self, country_name):
        url = "https://covid-193.p.rapidapi.com/statistics"
        params = {"country": country_name}
        headers = {
            "x-rapidapi-host": "covid-193.p.rapidapi.com",
            "x-rapidapi-key": self.covid_api_token
        }
        response = requests.get(url=url, params=params, headers=headers)
        return response.json()

    # method for rendering html format statistics
    @cached(cache)
    def __get_statistics_by_country_html(self, country_name):
        try:
            statistics_json = self.__get_statistics_by_country_from_api(country_name)
            with open("templates/country_statistics.html", encoding="UTF-8") as file:
                template = Template(file.read())
                return template.render(
                    country=statistics_json["response"][0]["country"].upper(),
                    date=ciso8601.parse_datetime(statistics_json["response"][0]["time"]).date(),
                    new_cases=statistics_json["response"][0]["cases"]["new"],
                    active_cases=statistics_json["response"][0]["cases"]["active"],
                    critical_cases=statistics_json["response"][0]["cases"]["critical"],
                    recovered_cases=statistics_json["response"][0]["cases"]["recovered"],
                    total_cases=statistics_json["response"][0]["cases"]["total"],
                    new_deaths=statistics_json["response"][0]["deaths"]["new"],
                    total_deaths=statistics_json["response"][0]["deaths"]["total"])
        except Exception as e:
            raise e

    # method for getting statistics by country_name
    def get_statistics_by_country_name(self, country_name, user_name):
        self.db_context.save_country_query(country_name, user_name)
        return self.__get_statistics_by_country_html(country_name)

    # method for getting statistics on user queries
    def get_statistics_of_users_queries(self):
        query_statistics = self.db_context.get_users_queries()
        with open("templates/query_statistics.html", encoding="UTF-8") as file:
            template = Template(file.read())
            return template.render(
                countries=query_statistics[0]["countries"],
                users=query_statistics[0]["users"]
            )

    def get_hidden_stats(self, days):
        last_days_info = self.db_context.get_last_days_info(int(days))

        unique_users_before_days = set(user["_id"] for user in last_days_info[0]["unique_users_before_days"])
        unique_users_requested_days = set(user["_id"] for user in last_days_info[0]["unique_users_requested_days"])
        new_users_requested_days = unique_users_requested_days.difference(unique_users_before_days)
        all_unique_users = unique_users_before_days.union(unique_users_requested_days)

        unique_countries_before_days = set(
            country["_id"] for country in last_days_info[0]["unique_countries_before_days"])
        unique_countries_requested_days = set(
            country["_id"] for country in last_days_info[0]["unique_countries_requested_days"])
        new_countries_requested_days = unique_countries_requested_days.difference(unique_countries_before_days)
        all_unique_countries = unique_countries_before_days.union(unique_countries_requested_days)

        stats = f"Total number of unique users: {len(all_unique_users)}" \
                f"\nNumber of unique users for the last {days} day(s): {len(unique_users_requested_days)}" \
                f"\nThe new ones: {len(new_users_requested_days)}" \
                f"\n\nTotal number of unique countries: {len(all_unique_countries)}" \
                f"\nNumber of unique countries for the last {days} day(s): {len(unique_countries_requested_days)}" \
                f"\nThe new ones: {len(new_countries_requested_days)}"
        return stats
