import os
from dependency_injector import providers, containers
from data.mongo_context import MongoDBContext
from services.country_service import CountryService
from services.statistics_service import StatisticsService


class Container(containers.DeclarativeContainer):
    """DI for development"""

    mongo_db_context = providers.Singleton(
        MongoDBContext,
        connection_string=os.getenv("CONNECTION_STRING"),
        db_name=os.getenv("DB_NAME")
    )
    country_service = providers.Singleton(
        CountryService,
        geo_api_key=os.getenv("GEO_NAME_API_KEY"),
        covid_api_token=os.getenv("COVID_STAT_API_TOKEN")
    )
    statistics_service = providers.Singleton(
        StatisticsService,
        covid_api_token=os.getenv("COVID_STAT_API_TOKEN"),
        db_context=mongo_db_context,
        country_service=country_service
    )
