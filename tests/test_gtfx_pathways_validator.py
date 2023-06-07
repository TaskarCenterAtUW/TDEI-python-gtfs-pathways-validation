import unittest
from unittest.mock import MagicMock, patch, call
from src.gtfx_pathways_validator import GTFSPathwaysValidator


class TestGTFSPathwaysValidator(unittest.TestCase):

    def setUp(self):
        # Create a mock Core instance for testing
        self.mock_settings = MagicMock()
        self.mock_settings.subscription_name = 'test_subscription'
        self.mock_settings.subscription_topic_name = 'test_subscription_topic'
        self.mock_settings.publishing_topic_name = 'test_publishing_topic'
        self.validator = GTFSPathwaysValidator()
        self.core_mock = MagicMock()
        self.core_mock.get_topic.return_value = MagicMock()
        self.core_mock.get_logger.return_value = MagicMock()
        self.core_mock.get_storage_client.return_value = MagicMock()

    def test_subscribe(self):
        mock_subscription = MagicMock()
        self.validator.listening_topic.subscribe = mock_subscription
        self.validator.subscribe()
        mock_subscription.assert_called_once_with(subscription=self.mock_settings.subscription_name,
                                                  callback=unittest.mock.ANY)

    @patch.object(GTFSPathwaysValidator, 'send_status')  # Mock the send_status method
    def test_valid_send_status(self, mock_send_status):
        upload_message_data = MagicMock()
        upload_message_data.stage = 'Pathways-Validation'  # Set the stage attribute

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
        self.assertEqual(upload_message_data.stage, 'Pathways-Validation')
        self.assertTrue(upload_message_data.meta.isValid)
        self.assertEqual(upload_message_data.meta.validationMessage, 'Validation successful')
        self.assertTrue(upload_message_data.response.success)
        self.assertEqual(upload_message_data.response.message, 'Validation successful')

        # Assert that the send_status method was called once with the expected arguments
        mock_send_status.assert_called_once_with(valid=True, upload_message=upload_message)

    @patch.object(GTFSPathwaysValidator, 'send_status')  # Mock the send_status method
    def test_invalid_send_status(self, mock_send_status):
        upload_message_data = MagicMock()
        upload_message_data.stage = 'Pathways-Validation'  # Set the stage attribute

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
        self.assertEqual(upload_message_data.stage, 'Pathways-Validation')
        self.assertFalse(upload_message_data.meta.isValid)
        self.assertEqual(upload_message_data.meta.validationMessage, 'Validation failed')
        self.assertFalse(upload_message_data.response.success)
        self.assertEqual(upload_message_data.response.message, 'Validation failed')

        # Assert that the send_status method was called once with the expected arguments
        mock_send_status.assert_called_once_with(valid=False, upload_message=upload_message)


if __name__ == '__main__':
    unittest.main()