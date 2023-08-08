from src.config import Settings
from src.gtfx_pathways_validator import GTFSPathwaysValidator
from python_ms_core import Core

class TestGTFSPathwaysIntegration(unittest.TestCase):
    def setUp(self):
        print('hello')
        this.settings = Settings()
        this.settings.subscription_topic_name = ''
        this.settings.subscription_name = ''
        this.settings.validation_topic = ''
        this.core = Core()
        

    def test_servicebus_receive(self):
        print('Have to test receiving of service bus')
        # create a gtfs_pathways_validator object
        gtfs_pathways_validator = GTFSPathwaysValidator()
        # Mock the listening and subscribe method

        topic = this.core.get_topic(this.settings.subscription_topic_name)
        # post a message to this topic
        msg = QueueMessage() # fill content for message
        topic.publish(msg)
        # Check if the message is received by gtfs_pathways_validator in 
        # the mocked method

    def test_servicebus_post(self):
        print('Have to test if the service can post')