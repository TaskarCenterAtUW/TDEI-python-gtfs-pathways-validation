import os
import json
import unittest
from unittest.mock import MagicMock
from src.serializer.gtfs_pathways_serializer import GTFSPathwaysUpload, GTFSPathwaysUploadData, Request, Meta, Response

current_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, '../')))
parent_dir = os.path.dirname(current_dir)

TEST_JSON_FILE = os.path.join(parent_dir, 'src/assets/test_pathways_payload.json')

TEST_FILE = open(TEST_JSON_FILE)
TEST_DATA = json.loads(TEST_FILE.read())


class TestGTFSPathwaysUpload(unittest.TestCase):

    def setUp(self):
        data = TEST_DATA
        self.upload = GTFSPathwaysUpload(data)

    def test_message(self):
        self.upload.message = 'New message'
        self.assertEqual(self.upload.message, 'New message')

    def test_message_type(self):
        self.assertEqual(self.upload.message_type, 'gtfs-pathways-upload')
        self.upload.message_type = 'New messageType'
        self.assertEqual(self.upload.message_type, 'New messageType')

    def test_message_id(self):
        self.upload.message_id = 'New messageId'
        self.assertEqual(self.upload.message_id, 'New messageId')

    def test_published_date(self):
        self.assertEqual(self.upload.published_date, '2023-02-08T08:33:36.267213Z')
        self.upload.published_date = '2023-05-24'
        self.assertEqual(self.upload.published_date, '2023-05-24')

    def test_data(self):
        self.assertIsInstance(self.upload.data, GTFSPathwaysUploadData)
        self.assertEqual(self.upload.data.stage, 'Pathways-Upload')
        self.upload.data.stage = 'Test stage'
        self.assertEqual(self.upload.data.stage, 'Test stage')

        # Add more assertions for other properties of GTFSPathwaysUploadData

    def test_to_json(self):
        self.upload.data.to_json = MagicMock(return_value={})
        json_data = self.upload.to_json()
        self.assertIsInstance(json_data, dict)
        self.assertEqual(json_data['message_type'], 'gtfs-pathways-upload')
        self.assertEqual(json_data['published_date'], '2023-02-08T08:33:36.267213Z')

    def test_data_from(self):
        message = TEST_DATA
        upload = GTFSPathwaysUpload.data_from(json.dumps(message))
        self.assertIsInstance(upload, GTFSPathwaysUpload)
        self.assertEqual(upload.message_type, 'gtfs-pathways-upload')
        self.assertEqual(upload.published_date, '2023-02-08T08:33:36.267213Z')


class TestGTFSPathwaysUploadData(unittest.TestCase):

    def setUp(self):
        data = TEST_DATA['data']
        self.upload_data = GTFSPathwaysUploadData(data)

    def test_stage(self):
        self.assertEqual(self.upload_data.stage, 'Pathways-Upload')
        self.upload_data.stage = 'Test stage'
        self.assertEqual(self.upload_data.stage, 'Test stage')

    def test_tdei_record_id(self):
        self.assertEqual(self.upload_data.tdei_record_id, 'c8c76e89f30944d2b2abd2491bd95337')
        self.upload_data.tdei_record_id = 'Test record ID'
        self.assertEqual(self.upload_data.tdei_record_id, 'Test record ID')

    def test_tdei_project_group_id(self):
        self.assertEqual(self.upload_data.tdei_project_group_id, '0b41ebc5-350c-42d3-90af-3af4ad3628fb')
        self.upload_data.tdei_project_group_id = 'Test Project Group ID'
        self.assertEqual(self.upload_data.tdei_project_group_id, 'Test Project Group ID')

    def test_user_id(self):
        self.assertEqual(self.upload_data.user_id, 'c59d29b6-a063-4249-943f-d320d15ac9ab')
        self.upload_data.user_id = 'Test user ID'
        self.assertEqual(self.upload_data.user_id, 'Test user ID')

    # Add more test cases for other properties of GTFSPathwaysUploadData


class TestRequest(unittest.TestCase):

    def setUp(self):
        data = TEST_DATA['data']
        self.request = Request(data)

    def test_tdei_project_group_id(self):
        self.assertEqual(self.request.tdei_project_group_id, '0b41ebc5-350c-42d3-90af-3af4ad3628fb')
        self.request.tdei_project_group_id = 'Test Project Group ID'
        self.assertEqual(self.request.tdei_project_group_id, 'Test Project Group ID')

    # Add more test cases for other properties of Request


class TestMeta(unittest.TestCase):

    def setUp(self):
        data = TEST_DATA['data']['meta']
        self.meta = Meta(data)

    def test_file_upload_path(self):
        self.assertEqual(self.meta.file_upload_path,
                         'https://tdeisamplestorage.blob.core.windows.net/gtfspathways/2023%2FFEBRUARY%2F0b41ebc5-350c-42d3-90af-3af4ad3628fb%2Fvalid_c8c76e89f30944d2b2abd2491bd95337.zip')
        self.meta.file_upload_path = 'Test file path'
        self.assertEqual(self.meta.file_upload_path, 'Test file path')

    # Add more test cases for other properties of Meta


class TestResponse(unittest.TestCase):

    def setUp(self):
        data = TEST_DATA['data']['response']
        self.response = Response(data)

    def test_success(self):
        self.assertEqual(self.response.success, True)
        self.response.success = False
        self.assertEqual(self.response.success, False)


if __name__ == '__main__':
    unittest.main()
