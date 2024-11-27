import unittest
from src.models.file_upload_msg import FileUploadMsg, IncomingData


class TestFileUploadMsg(unittest.TestCase):

    def test_from_dict_with_valid_data(self):
        # Arrange
        input_data = {
            'messageId': '12345',
            'messageType': 'file_upload',
            'data': {
                'file_upload_path': '/path/to/file',
                'user_id': 'user_001',
                'tdei_project_group_id': 'project_123'
            }
        }

        # Act
        result = FileUploadMsg.from_dict(input_data)

        # Assert
        self.assertEqual(result.messageId, '12345')
        self.assertEqual(result.messageType, 'file_upload')
        self.assertIsInstance(result.data, IncomingData)
        self.assertEqual(result.data.file_upload_path, '/path/to/file')
        self.assertEqual(result.data.user_id, 'user_001')
        self.assertEqual(result.data.tdei_project_group_id, 'project_123')

    def test_from_dict_with_partial_data(self):
        # Arrange
        input_data = {
            'messageId': '12345',
            'messageType': 'file_upload',
            'data': {
                'file_upload_path': '/path/to/file',
                'user_id': 'user_001'
            }
        }

        # Act
        result = FileUploadMsg.from_dict(input_data)

        # Assert
        self.assertEqual(result.messageId, '12345')
        self.assertEqual(result.messageType, 'file_upload')
        self.assertIsInstance(result.data, IncomingData)
        self.assertEqual(result.data.file_upload_path, '/path/to/file')
        self.assertEqual(result.data.user_id, 'user_001')
        self.assertEqual(result.data.tdei_project_group_id, '')

    def test_from_dict_with_no_data_key(self):
        # Arrange
        input_data = {
            'messageId': '12345',
            'messageType': 'file_upload'
        }

        # Act
        result = FileUploadMsg.from_dict(input_data)

        # Assert
        self.assertEqual(result.messageId, '12345')
        self.assertEqual(result.messageType, 'file_upload')
        self.assertIsNone(result.data)

    def test_from_dict_with_empty_dict(self):
        # Arrange
        input_data = {}

        # Act
        result = FileUploadMsg.from_dict(input_data)

        # Assert
        self.assertIsNone(result.messageId)
        self.assertIsNone(result.messageType)
        self.assertIsNone(result.data)

    def test_incoming_data_default_tdei_project_group_id(self):
        # Arrange
        incoming_data = IncomingData(
            file_upload_path='/path/to/file',
            user_id='user_001'
        )

        # Assert
        self.assertEqual(incoming_data.file_upload_path, '/path/to/file')
        self.assertEqual(incoming_data.user_id, 'user_001')
        self.assertEqual(incoming_data.tdei_project_group_id, '')

if __name__ == '__main__':
    unittest.main()
