# class to hold the file upload message
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class IncomingData:
    file_upload_path:str
    user_id:str 
    tdei_project_group_id: str

@dataclass
class FileUploadMsg: 
    messageId:str 
    messageType: str
    data: IncomingData
    
    @classmethod
    def from_dict(cls, data:Dict):
        incoming_data = data.get('data')
        if incoming_data:
            theData = IncomingData(**incoming_data)
        else:
            theData = None
        return cls(
            messageId = data.get('messageId'),
            messageType = data.get('messageType'),
            data = theData
        )
