import os
from dotenv import load_dotenv
from pydantic import BaseSettings
import uuid

load_dotenv()

# Where scripts/download-gtfs-validator.sh puts MobilityData's validator by default
DEFAULT_GTFS_VALIDATOR_JAR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib',
                                          'gtfs-validator-cli.jar')


class Settings(BaseSettings):
    app_name: str = 'gtfs-flex-validation-service-python'
    request_topic_name: str = os.environ.get('REQUEST_TOPIC', None)
    response_topic_name: str = os.environ.get('RESPONSE_TOPIC', None)
    request_subscription: str = os.environ.get('REQUEST_SUBSCRIPTION', None)
    storage_container_name: str = os.environ.get('CONTAINER_NAME', 'gtfspathways')
    max_concurrent_messages: int = os.environ.get('MAX_CONCURRENT_MESSAGES', 2)
    # MobilityData's GTFS validator, run locally (see scripts/download-gtfs-validator.sh)
    gtfs_validator_jar: str = os.environ.get('GTFS_VALIDATOR_JAR', DEFAULT_GTFS_VALIDATOR_JAR)
    gtfs_validator_country_code: str = os.environ.get('GTFS_VALIDATOR_COUNTRY_CODE', 'us')
    gtfs_validator_timeout: int = os.environ.get('GTFS_VALIDATOR_TIMEOUT', 900)  # seconds
    java_path: str = os.environ.get('JAVA_PATH', 'java')
    
    def get_unique_id(self) -> str:
        return str(uuid.uuid4())