import unittest
from unittest.mock import MagicMock, patch, call
from src.pathways_queue_worker import PathwaysQueueWorker


class TestPathwaysQueueWorker(unittest.TestCase):

    @patch('src.pathways_queue_worker.Settings')
    @patch('src.pathways_queue_worker.Core')
    def setUp(self, mock_core, mock_settings):
        mock_settings.return_value.request_subscription = 'test_subscription'
        mock_settings.return_value.request_topic_name = 'test_request_topic'
        mock_settings.return_value.response_topic_name = 'test_response_topic'
        mock_settings.return_value.max_concurrent_messages = 10
        mock_settings.return_value.get_unique_id.return_value = '123'
        mock_settings.return_value.container_name = 'test_container'

        # Mock Core
        mock_core.return_value.get_topic.return_value = MagicMock()
        mock_core.return_value.get_storage_client.return_value = MagicMock()

        # Initialize PathwaysQueueWorker with mocked dependencies
        self.validator = PathwaysQueueWorker()
        self.validator.storage_client = MagicMock()
        self.validator.container_name = 'test_container'
        self.sample_message = {
            'messageId': '1234',
            'data': {
                'file_upload_path': 'https://tdeisamplestorage.blob.core.windows.net/pathways/tests/success_1_all_attrs.zip',
                'user_id': 'c59d29b6-a063-4249-943f-d320d15ac9ab',
                'tdei_project_group_id': '0b41ebc5-350c-42d3-90af-3af4ad3628fb'
            }
        }

    @patch('src.pathways_queue_worker.QueueMessage')
    @patch('src.pathways_queue_worker.FileUploadMsg')
    def test_subscribe_with_valid_message(self, mock_request_message, mock_queue_message):
        # Arrange
        mock_message = MagicMock()
        mock_queue_message.to_dict.return_value = self.sample_message
        mock_request_message.from_dict.return_value = mock_request_message
        self.validator.process_message = MagicMock()

        # Act
        self.validator.subscribe()
        callback = self.validator.request_topic.subscribe.call_args[1]['callback']
        callback(mock_message)

        # Assert
        self.validator.process_message.assert_called_once_with(mock_request_message)

    @patch('src.pathways_queue_worker.PathwaysFeedValidation')
    def test_process_message_with_valid_file_path(self, mock_validation_instance):
        # Arrange
        mock_request_message = MagicMock()
        mock_request_message.data.file_upload_path = 'test_dataset_url'
        mock_request_message.data.tdei_project_group_id = 'tdei_project_group_id'

        mock_pathways_validation_instance = mock_validation_instance.return_value
        mock_pathways_validation_instance.validate.return_value = True, 'Validation successful'

        self.validator.send_status = MagicMock()

        # Act
        self.validator.process_message(mock_request_message)

        # Assert

        self.validator.send_status.assert_called_once_with(valid=True, upload_message=mock_request_message,
                                                           validation_message='Validation successful',
                                                           report=mock_pathways_validation_instance.report,
                                                           report_url=mock_pathways_validation_instance.report_url)

    def test_process_message_with_no_file_path(self):
        # Arrange
        mock_request_message = MagicMock()
        mock_request_message.data.file_upload_path = ''
        mock_request_message.data.tdei_project_group_id = 'tdei_project_group_id'

        self.validator.send_status = MagicMock()

        # Act
        self.validator.process_message(mock_request_message)

        # Assert

        self.validator.send_status.assert_called_once_with(valid=False, upload_message=mock_request_message,
                                                           validation_message='No file Path found in message!')

    @patch('src.pathways_queue_worker.PathwaysFeedValidation')
    def test_process_message_with_exception(self, mock_validation_instance):
        # Arrange
        mock_request_message = MagicMock()
        mock_request_message.data.file_upload_path = 'test_dataset_url'
        mock_request_message.data.tdei_project_group_id = 'tdei_project_group_id'

        mock_validation_instance.side_effect = Exception('Some error occurred')

        self.validator.send_status = MagicMock()

        # Act
        self.validator.process_message(mock_request_message)

        # Assert

        self.validator.send_status.assert_called_once_with(valid=False, upload_message=mock_request_message,
                                                           validation_message='Some error occurred')

    @patch('src.pathways_queue_worker.QueueMessage')
    def test_send_status_success(self, mock_queue_message):
        # Arrange
        mock_request_message = MagicMock()
        mock_response_topic = self.validator.core.get_topic.return_value
        mock_data = {'messageId': '1234', 'messageType': 'test', 'data': {'success': True}}
        mock_queue_message.data_from.return_value = mock_data

        # Act
        self.validator.send_status(
            valid=True,
            upload_message=mock_request_message,
            validation_message='Validation successful'
        )

        # Assert
        mock_queue_message.data_from.assert_called_once()
        mock_response_topic.publish.assert_called_once_with(data=mock_data)

    @patch('src.pathways_queue_worker.QueueMessage')
    def test_send_status_includes_the_report(self, mock_queue_message):
        # Arrange
        mock_report = MagicMock(summary={'valid': True}, validator_version='8.0.1')

        # Act
        self.validator.send_status(
            valid=True,
            upload_message=MagicMock(),
            validation_message='',
            report=mock_report,
            report_url='https://reports/feed-report.zip'
        )

        # Assert
        data = mock_queue_message.data_from.call_args[0][0]['data']
        self.assertEqual(data['report_url'], 'https://reports/feed-report.zip')
        self.assertEqual(data['report_summary'], {'valid': True})
        self.assertEqual(data['package']['gtfs-validator'], '8.0.1')

    @patch('src.pathways_queue_worker.QueueMessage')
    def test_send_status_without_a_report(self, mock_queue_message):
        # Act
        self.validator.send_status(valid=False, upload_message=MagicMock(), validation_message='Error')

        # Assert
        data = mock_queue_message.data_from.call_args[0][0]['data']
        self.assertIsNone(data['report_url'])
        self.assertIsNone(data['report_summary'])

    @patch('src.pathways_queue_worker.threading.Thread')
    def test_stop_listening(self, mock_thread):
        # Arrange
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        self.validator.listening_thread = mock_thread_instance

        # Act
        result = self.validator.stop_listening()

        # Assert
        mock_thread_instance.join.assert_called_once_with(timeout=0)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
