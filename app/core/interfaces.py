from abc import ABC, abstractmethod
from fastapi import UploadFile
from typing import Dict, Any

class IResumeService(ABC):
    @abstractmethod
    async def upload_and_parse(self, file: UploadFile) -> Dict[str, Any]:
        pass