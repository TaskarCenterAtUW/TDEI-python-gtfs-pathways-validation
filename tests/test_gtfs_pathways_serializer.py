import unittest
from unittest.mock import MagicMock
from src.serializer.gtfs_pathways_serializer import GTFSPathwaysUpload, GTFSPathwaysUploadData, Request, Meta, Response


class TestGTFSPathwaysUpload(unittest.TestCase):

    def setUp(self):
        data = {
            'data': {
                'polygon': {},
                'request': {},
                'meta': {},
                'response': {},
                'tdei_record_id': '',
                'tdei_org_id': '',
                'user_id': ''
            },
            'message': 'Test message',
            'messageType': 'Test messageType',
            'messageId': 'Test messageId',
            'publishedDate': '2023-05-23'
        }
        self.upload = GTFSPathwaysUpload(data)

    def test_message(self):
        self.assertEqual(self.upload.message, 'Test message')
        self.upload.message = 'New message'
        self.assertEqual(self.upload.message, 'New message')

    def test_message_type(self):
        self.assertEqual(self.upload.message_type, 'Test messageType')
        self.upload.message_type = 'New messageType'
        self.assertEqual(self.upload.message_type, 'New messageType')

    def test_message_id(self):
        self.assertEqual(self.upload.message_id, 'Test messageId')
        self.upload.message_id = 'New messageId'
        self.assertEqual(self.upload.message_id, 'New messageId')

    def test_published_date(self):
        self.assertEqual(self.upload.published_date, '2023-05-23')
        self.upload.published_date = '2023-05-24'
        self.assertEqual(self.upload.published_date, '2023-05-24')

    def test_data(self):
        self.assertIsInstance(self.upload.data, GTFSPathwaysUploadData)
        self.assertEqual(self.upload.data.stage, '')
        self.upload.data.stage = 'Test stage'
        self.assertEqual(self.upload.data.stage, 'Test stage')

        # Add more assertions for other properties of GTFSPathwaysUploadData

    def test_to_json(self):
        self.upload.data.to_json = MagicMock(return_value={})
        json_data = self.upload.to_json()
        self.assertIsInstance(json_data, dict)
        self.assertEqual(json_data['message'], 'Test message')
        self.assertEqual(json_data['messageType'], 'Test messageType')
        self.assertEqual(json_data['messageId'], 'Test messageId')
        self.assertEqual(json_data['publishedDate'], '2023-05-23')
        self.assertEqual(self.upload.data.to_json.call_count, 1)

    def test_data_from(self):
        message = {
            'data': {
                'polygon': {},
                'request': {},
                'meta': {},
                'response': {},
                'tdei_record_id': '',
                'tdei_org_id': '',
                'user_id': ''
            },
            'message': 'Test message',
            'messageType': 'Test messageType',
            'messageId': 'Test messageId',
            'publishedDate': '2023-05-23'
        }
        upload = GTFSPathwaysUpload.data_from(json.dumps(message))
        self.assertIsInstance(upload, GTFSPathwaysUpload)
        self.assertEqual(upload.message, 'Test message')
        self.assertEqual(upload.message_type, 'Test messageType')
        self.assertEqual(upload.message_id, 'Test messageId')
        self.assertEqual(upload.published_date, '2023-05-23')


class TestGTFSPathwaysUploadData(unittest.TestCase):

    def setUp(self):
        data = {
            'polygon': {},
            'request': {},
            'meta': {},
            'response': {},
            'tdei_record_id': '',
            'tdei_org_id': '',
            'user_id': ''
        }
        self.upload_data = GTFSPathwaysUploadData(data)

    def test_stage(self):
        self.assertEqual(self.upload_data.stage, '')
        self.upload_data.stage = 'Test stage'
        self.assertEqual(self.upload_data.stage, 'Test stage')

    def test_tdei_record_id(self):
        self.assertEqual(self.upload_data.tdei_record_id, '')
        self.upload_data.tdei_record_id = 'Test record ID'
        self.assertEqual(self.upload_data.tdei_record_id, 'Test record ID')

    def test_tdei_org_id(self):
        self.assertEqual(self.upload_data.tdei_org_id, '')
        self.upload_data.tdei_org_id = 'Test org ID'
        self.assertEqual(self.upload_data.tdei_org_id, 'Test org ID')

    def test_user_id(self):
        self.assertEqual(self.upload_data.user_id, '')
        self.upload_data.user_id = 'Test user ID'
        self.assertEqual(self.upload_data.user_id, 'Test user ID')

    # Add more test cases for other properties of GTFSPathwaysUploadData


class TestRequest(unittest.TestCase):

    def setUp(self):
        data = {
            'tdei_org_id': '',
            'tdei_station_id': '',
            'collected_by': '',
            'collection_date': '',
            'collection_method': '',
            'valid_from': '',
            'valid_to': '',
            'data_source': '',
            'polygon': {},
            'pathways_schema_version': ''
        }
        self.request = Request(data)

    def test_tdei_org_id(self):
        self.assertEqual(self.request.tdei_org_id, '')
        self.request.tdei_org_id = 'Test org ID'
        self.assertEqual(self.request.tdei_org_id, 'Test org ID')

    # Add more test cases for other properties of Request


class TestMeta(unittest.TestCase):

    def setUp(self):
        data = {
            'file_upload_path': '',
            'isValid': False,
            'validationMessage': '',
            'validationTime': 90
        }
        self.meta = Meta(data)

    def test_file_upload_path(self):
        self.assertEqual(self.meta.file_upload_path, '')
        self.meta.file_upload_path = 'Test file path'
        self.assertEqual(self.meta.file_upload_path, 'Test file path')

    # Add more test cases for other properties of Meta


class TestResponse(unittest.TestCase):

    def setUp(self):
        data = {
            'success': False,
            'message': ''
        }
        self.response = Response(data)

    def test_success(self):
        self.assertEqual(self.response.success, False)
        self.response.success = True
        self.assertEqual(self.response.success, True)

    # Add more test cases for other properties of Response


if __name__ == '__main__':
    unittest.main()
