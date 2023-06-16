import os
import datetime
import json
import time
import uuid
from python_ms_core import Core
from python_ms_core.core.queue.models.queue_message import QueueMessage
from pydantic import BaseSettings
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_JSON_FILE = os.path.join(ROOT_DIR, 'tests.json')
TEST_FILE = open(TEST_JSON_FILE)
TEST_DATA = json.loads(TEST_FILE.read())

TESTS = TEST_DATA['Tests']

load_dotenv()


class Settings(BaseSettings):
    publishing_topic_name: str = os.environ.get('VALIDATION_TOPIC', None)
    subscription_topic_name: str = os.environ.get('UPLOAD_TOPIC', None)
    subscription_name: str = os.environ.get('UPLOAD_SUBSCRIPTION', None)
    container_name: str = os.environ.get('CONTAINER_NAME', 'tdei-storage-test')


def post_message_to_topic(msg: dict, core, settings: Settings):
    publish_topic = core.get_topic(topic_name=settings.publishing_topic_name)
    data = QueueMessage.data_from(msg)
    publish_topic.publish(data=data)


def do_test(test, core, settings: Settings):
    print(f'Performing tests :{test["Name"]}')
    storage_client = core.get_storage_client()

    container = storage_client.get_container(container_name=settings.container_name)
    basename = os.path.basename(test['Input_file'])

    suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")

    base_name, base_ext = os.path.splitext(basename)
    file_name = "_".join([base_name, suffix]) + base_ext
    test_file = container.create_file(f'test_upload/{file_name}')  # Removed mime-type

    input_file = os.path.join(ROOT_DIR, test['Input_file'])
    # Uploading file to blob storage
    with open(input_file, 'rb') as msg_file:
        test_file.upload(msg_file)
        blob_url = test_file.get_remote_url()
        print(f'Performing tests :{test["Name"]}:{blob_url}')
    message_id = uuid.uuid1().hex[0:24]
    # Reading the input file
    input_data = open(input_file)
    data = json.load(input_data)
    data['message'] = test['Name']
    upload_message = {
        'messageId': message_id,
        'message': test['Name'],
        'messageType': 'gtfs-pathways-upload',
        'data': data
    }
    # Publishing message to topic
    post_message_to_topic(upload_message, core, settings)


def subscribe(core, settings: Settings):
    def process(message) -> None:
        parsed_message = message.__dict__
        message = parsed_message['message']
        parsed_data = parsed_message['data']
        test_detail = [item for item in TESTS if item.get('Name') == message]
        if len(test_detail) > 0:
            if test_detail[0]['Result'] == parsed_data['response']['success']:
                print(f'Performing tests :{message}:PASSED\n')
            else:
                print(f'Performing tests :{message}:FAILED\n')
        else:
            # print(parsed_message)
            print('Message Received from NodeJS publisher. \n')

    try:
        listening_topic = core.get_topic(topic_name=settings.subscription_topic_name)
        listening_topic.subscribe(subscription=settings.subscription_name, callback=process)
    except Exception as e:
        print(e)
        print('Tests Done!')


def test_harness(core):
    settings = Settings()
    subscribe(core, settings=settings)
    for test in TESTS:
        do_test(test, core, settings)


if __name__ == "__main__":
    core = Core()
    time.sleep(1)
    print(f'Performing tests :')
    test_harness(core)
    time.sleep(30)
    print('Tests Completed!\n')
    os._exit(0)
