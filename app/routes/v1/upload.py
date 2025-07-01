from fastapi import APIRouter, UploadFile, Depends

from app.core.interfaces import IResumeService
from app.core.resume_service import ResumeService

router = APIRouter(
    prefix="/upload",
    tags=["upload"],
)

def get_resume_service() -> IResumeService:
    return ResumeService()

# 只保留核心上传接口
@router.post("/")
async def upload_resume(
    file: UploadFile,
    service: IResumeService = Depends(get_resume_service)
):
    return await service.upload_and_parse(file)