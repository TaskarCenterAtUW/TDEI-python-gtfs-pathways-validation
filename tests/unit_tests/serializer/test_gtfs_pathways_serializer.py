import unittest
from src.serializer.gtfs_pathways_serializer import (
    GTFSPathwaysUpload,
    GTFSPathwaysUploadData,
    Request,
    Meta,
    Response,
    remove_underscore
)

class TestGTFSPathwaysUpload(unittest.TestCase):
    def test_gtfs_pathways_upload_initialization_with_data(self):
        data = {
            'messageId': '12345',
            'messageType': 'file_upload',
            'message': 'Test message',
            'publishedDate': '2024-11-20',
            'data': {
                'stage': 'stage1',
                'tdei_record_id': 'record123',
                'tdei_project_group_id': 'group123',
                'user_id': 'user123',
                'request': {
                    'tdei_project_group_id': 'group123',
                    'tdei_station_id': 'station123',
                    'collected_by': 'user123',
                    'collection_date': '2024-11-20',
                    'collection_method': 'method1',
                    'valid_from': '2024-11-20',
                    'valid_to': '2024-11-21',
                    'data_source': 'source1',
                    'polygon': {},
                    'pathways_schema_version': 'v1.0',
                },
                'meta': {'file_upload_path': '/path/to/file'},
                'response': {'success': True, 'message': 'Validation successful'},
            },
        }
        upload = GTFSPathwaysUpload(data=data)

        self.assertEqual(upload.message_id, '12345')
        self.assertEqual(upload.message_type, 'file_upload')
        self.assertEqual(upload.message, 'Test message')
        self.assertEqual(upload.published_date, '2024-11-20')
        self.assertIsInstance(upload.data, GTFSPathwaysUploadData)
        self.assertEqual(upload.data.stage, 'stage1')
        self.assertEqual(upload.data.tdei_record_id, 'record123')
        self.assertEqual(upload.data.tdei_project_group_id, 'group123')
        self.assertEqual(upload.data.user_id, 'user123')

    def test_gtfs_pathways_upload_initialization_without_data(self):
        data = {}
        upload = GTFSPathwaysUpload(data=data)

        self.assertEqual(upload.message_id, '')
        self.assertIsNone(upload.message_type)
        self.assertIsNone(upload.message)
        self.assertIsNone(upload.published_date)
        self.assertEqual(upload.data, {})


    def test_remove_underscore(self):
        self.assertEqual(remove_underscore('_fieldName'), 'fieldName')
        self.assertEqual(remove_underscore('fieldName'), 'fieldName')

    def test_request_initialization(self):
        request_data = {
            'tdei_project_group_id': 'group123',
            'tdei_station_id': 'station123',
            'collected_by': 'user123',
            'collection_date': '2024-11-20',
            'collection_method': 'method1',
            'valid_from': '2024-11-20',
            'valid_to': '2024-11-21',
            'data_source': 'source1',
            'polygon': {},
            'pathways_schema_version': 'v1.0',
        }
        request = Request(data=request_data)

        self.assertEqual(request.tdei_project_group_id, 'group123')
        self.assertEqual(request.tdei_station_id, 'station123')
        self.assertEqual(request.collected_by, 'user123')
        self.assertEqual(request.collection_date, '2024-11-20')
        self.assertEqual(request.collection_method, 'method1')
        self.assertEqual(request.valid_from, '2024-11-20')
        self.assertEqual(request.valid_to, '2024-11-21')
        self.assertEqual(request.data_source, 'source1')
        self.assertEqual(request.pathways_schema_version, 'v1.0')

    def test_meta_initialization(self):
        meta_data = {'file_upload_path': '/path/to/file'}
        meta = Meta(data=meta_data)

        self.assertEqual(meta.file_upload_path, '/path/to/file')
        self.assertFalse(meta.isValid)
        self.assertEqual(meta.validationMessage, '')

    def test_response_initialization(self):
        response_data = {'success': True, 'message': 'Validation successful'}
        response = Response(data=response_data)

        self.assertTrue(response.success)
        self.assertEqual(response.message, 'Validation successful')


if __name__ == '__main__':
    unittest.main()
