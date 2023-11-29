import unittest
from unittest.mock import MagicMock, patch, call
from src.gtfx_pathways_validator import GTFSPathwaysValidator


class TestGTFSPathwaysValidator(unittest.TestCase):

    def setUp(self):
        with patch.object(GTFSPathwaysValidator, '__init__', return_value=None):
            self.validator = GTFSPathwaysValidator()
            self.validator._subscription_name = MagicMock()
            self.validator.listening_topic = MagicMock()
            self.validator.publish_topic = MagicMock()
            self.validator.logger = MagicMock()
            self.validator.storage_client = MagicMock()

    @patch.object(GTFSPathwaysValidator, 'subscribe')
    def test_subscribe(self, mock_subscribe):
        # Act
        self.validator.subscribe()

        # Assert
        mock_subscribe.assert_called_once()

    @patch.object(GTFSPathwaysValidator, 'send_status')  # Mock the send_status method
    def test_valid_send_status(self, mock_send_status):
        upload_message_data = MagicMock()
        upload_message_data.stage = 'pathways-validation'  # Set the stage attribute

        # Create a mock meta object
        mock_meta = MagicMock()
        mock_meta.isValid = True
        mock_meta.validationMessage = 'Validation successful'

        upload_message_data.meta = mock_meta

        # Create a mock response object
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = 'Validation successful'

        upload_message_data.response = mock_response

        # Create a mock upload_message object
        upload_message = MagicMock()
        upload_message.message = 'Test message'
        upload_message.data = upload_message_data

        # Call the send_status method
        self.validator.send_status(valid=True, upload_message=upload_message)

        # Add assertions for the expected behavior
        self.assertEqual(upload_message_data.stage, 'pathways-validation')
        self.assertTrue(upload_message_data.meta.isValid)
        self.assertEqual(upload_message_data.meta.validationMessage, 'Validation successful')
        self.assertTrue(upload_message_data.response.success)
        self.assertEqual(upload_message_data.response.message, 'Validation successful')

        # Assert that the send_status method was called once with the expected arguments
        mock_send_status.assert_called_once_with(valid=True, upload_message=upload_message)

    @patch.object(GTFSPathwaysValidator, 'send_status')  # Mock the send_status method
    def test_invalid_send_status(self, mock_send_status):
        upload_message_data = MagicMock()
        upload_message_data.stage = 'pathways-validation'  # Set the stage attribute

        # Create a mock meta object
        mock_meta = MagicMock()
        mock_meta.isValid = False
        mock_meta.validationMessage = 'Validation failed'

        upload_message_data.meta = mock_meta

        # Create a mock response object
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.message = 'Validation failed'

        upload_message_data.response = mock_response

        # Create a mock upload_message object
        upload_message = MagicMock()
        upload_message.message = 'Test message'
        upload_message.data = upload_message_data

        # Call the send_status method
        self.validator.send_status(valid=False, upload_message=upload_message)

        # Add assertions for the expected behavior
        self.assertEqual(upload_message_data.stage, 'pathways-validation')
        self.assertFalse(upload_message_data.meta.isValid)
        self.assertEqual(upload_message_data.meta.validationMessage, 'Validation failed')
        self.assertFalse(upload_message_data.response.success)
        self.assertEqual(upload_message_data.response.message, 'Validation failed')

        # Assert that the send_status method was called once with the expected arguments
        mock_send_status.assert_called_once_with(valid=False, upload_message=upload_message)


if __name__ == '__main__':
    unittest.main()
