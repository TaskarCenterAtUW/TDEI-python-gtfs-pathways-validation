import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    app_name: str = 'gtfs-flex-validation-service-python'
    subscription_topic_name: str = os.environ.get('UPLOAD_TOPIC', None)
    publishing_topic_name: str = os.environ.get('VALIDATION_TOPIC', None)
    subscription_name: str = os.environ.get('UPLOAD_SUBSCRIPTION', None)
    validation_topic: str = os.environ.get('VALIDATION_TOPIC', None)
    storage_container_name: str = os.environ.get('CONTAINER_NAME', 'tdei-storage-test')
