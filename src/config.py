import os
from dotenv import load_dotenv
from pydantic import BaseSettings
import uuid

load_dotenv()


class Settings(BaseSettings):
    app_name: str = 'gtfs-flex-validation-service-python'
    request_topic_name: str = os.environ.get('REQUEST_TOPIC', None)
    response_topic_name: str = os.environ.get('RESPONSE_TOPIC', None)
    request_subscription: str = os.environ.get('REQUEST_SUBSCRIPTION', None)
    storage_container_name: str = os.environ.get('CONTAINER_NAME', 'gtfspathways')

    def get_unique_id(self) -> str:
        return str(uuid.uuid4())