import logging
import uuid
import urllib.parse
from python_ms_core import Core
from python_ms_core.core.queue.models.queue_message import QueueMessage
from .config import Settings
from .gtfs_pathways_validation import GTFSPathwaysValidation
from .serializer.gtfs_pathways_serializer import GTFSPathwaysUpload
from .models.file_upload_msg import FileUploadMsg
import threading

logging.basicConfig()
logger = logging.getLogger('PATHWAYS_VALIDATOR')
logger.setLevel(logging.INFO)


class GTFSPathwaysValidator:
    _settings = Settings()

    def __init__(self):
        core = Core()
        settings = Settings()
        self._subscription_name = settings.request_subscription
        self.request_topic = core.get_topic(topic_name=settings.request_topic_name)
        self.response_topic = core.get_topic(topic_name=settings.response_topic_name)
        self.logger = core.get_logger()
        self.storage_client = core.get_storage_client()
        self.subscribe()

    def subscribe(self) -> None:
        # Process the incoming message
        def process(message) -> None:
            if message is not None:
                gtfs_upload_message = QueueMessage.to_dict(message)
                upload_msg = FileUploadMsg.from_dict(gtfs_upload_message)
                logger.info(upload_msg)
                process_thread = threading.Thread(target=self.process_message,args=[upload_msg])
                process_thread.start()
            else:
                logger.info(' No Message')

        self.request_topic.subscribe(subscription=self._subscription_name, callback=process)

    def process_message(self, upload_msg: FileUploadMsg) -> None:
        file_upload_path = urllib.parse.unquote(upload_msg.data.file_upload_path)
        logger.info(f' Received message for Project Group: {upload_msg.data.tdei_project_group_id}')
        logger.info(file_upload_path)
        if file_upload_path:
            # Do the validation in the other class
            validator = GTFSPathwaysValidation(file_path=file_upload_path, storage_client=self.storage_client)
            validation = validator.validate()
            self.send_status(valid=validation[0], upload_message=upload_msg,
                                validation_message=validation[1])
        else:
            logger.info(' No file Path found in message!')

    def send_status(self, valid: bool, upload_message: FileUploadMsg, validation_message: str = '') -> None:
        # upload_message.data.stage = 'pathways-validation'
        # upload_message.data.meta.isValid = valid
        # upload_message.data.meta.validationMessage = validation_message or 'Validation successful'
        # upload_message.data.response.success = valid
        # upload_message.data.response.message = validation_message or 'Validation successful'
        # message_id = uuid.uuid1().hex[0:24]
        response_message = {
             "file_upload_path": upload_message.data.file_upload_path,
      "user_id": upload_message.data.user_id ,
      "tdei_project_group_id": upload_message.data.tdei_project_group_id,
      "success": valid,
      "message": validation_message
        }
        logger.info(
            f' Publishing new message with ID: {upload_message.messageId} with status: {valid} and Message: {validation_message}')
        data = QueueMessage.data_from({
            'messageId': upload_message.messageId,
            'message':  'Validation complete',
            'messageType': upload_message.messageType,
            'data': response_message
        })
        self.response_topic.publish(data=data)
        return
