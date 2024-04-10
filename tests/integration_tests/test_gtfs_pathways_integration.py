import unittest
import os
import json
import time
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
import asyncio
from urllib.parse import urlparse

# Execute to apply environment variable overrides
load_dotenv()

os.environ['UPLOAD_TOPIC'] = 'temp-upload'
os.environ['UPLOAD_SUBSCRIPTION'] = 'upload-validation-processor'
os.environ['VALIDATION_TOPIC'] = 'temp-validation'

from src.gtfx_pathways_validator import GTFSPathwaysValidator
from python_ms_core import Core
from python_ms_core.core.queue.models.queue_message import QueueMessage

TEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_JSON_FILE = os.path.join(TEST_DIR, 'test_harness/test_files/pathways_test_case2.json')


class TestGTFSPathwaysIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()
        cls.upload_topic_name = os.environ['UPLOAD_TOPIC']
        cls.upload_subscription_name = os.environ['UPLOAD_SUBSCRIPTION']
        cls.validation_topic_name = os.environ['VALIDATION_TOPIC']

    def setUp(self):
        self.test_data = self.read_test_data()

    @staticmethod
    def read_test_data():
        with open(TEST_JSON_FILE, 'r') as test_file:
            test_data = json.loads(test_file.read())
        return test_data

    def tearDown(self):
        pass

    @patch.object(GTFSPathwaysValidator, 'subscribe', new=MagicMock())
    def test_subscribe_to_upload_topic(self):
        if os.environ['QUEUECONNECTION'] is None:
            self.fail('QUEUECONNECTION environment not set')
        validator = GTFSPathwaysValidator()
        upload_topic = self.core.get_topic(topic_name=self.upload_topic_name)
        message = QueueMessage.data_from({'message': '', 'data': self.test_data})
        upload_topic.publish(data=message)
        time.sleep(0.5)  # Wait to get the callback
        validator.subscribe.assert_called_once()

    @patch.object(GTFSPathwaysValidator, 'subscribe', new=MagicMock())
    async def test_servicebus_receive(self):
        if os.environ['QUEUECONNECTION'] is None:
            self.fail('QUEUECONNECTION environment not set')
        validator = GTFSPathwaysValidator()
        subscribe_function = MagicMock()
        message = QueueMessage.data_from({'message': '', 'data': self.test_data})
        validator.response_topic.publish(data=message)
        validation_topic = self.core.get_topic(topic_name=self.validation_topic_name)
        async with validation_topic.subscribe(subscription='temp-validation-result', callback=subscribe_function):
            await asyncio.sleep(0.5)  # Wait for callback
            subscribe_function.assert_called_once()
            validator.subscribe.assert_called_once()

    def test_file_entity(self):
        test_file_url = 'https://tdeisamplestorage.blob.core.windows.net/osw/2023/APRIL/66c85a5a-2335-4b97-a0a3-0bb93cba1ae5/osw-test-upload_19df12452cae4da5a71db3fa276f4f5e.zip'
        url = urlparse(test_file_url)
        file_path = url.path
        file_components = file_path.split('/')
        container_name = file_components[1]
        file = self.core.get_storage_client().get_file_from_url(container_name=container_name, full_url=test_file_url)
        content = file.get_stream()
        self.assertTrue(content)


if __name__ == '__main__':
    unittest.main()
