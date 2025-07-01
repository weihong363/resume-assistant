from fastapi import UploadFile
from typing import Dict, Any
from app.core.interfaces import IResumeService
from app.core.zh_resume_parser import ChineseResumeParser
import os

class ResumeService(IResumeService):
    def __init__(self):
        self.parser = ChineseResumeParser()
        
    async def upload_and_parse(self, file: UploadFile) -> Dict[str, Any]:
        # 保存临时文件
        temp_path = f'/tmp/{file.filename}'
        with open(temp_path, 'wb') as f:
            f.write(await file.read())
        await file.seek(0)
        
        try:
            # 读取文件内容
            content = await self._read_file_content(temp_path)
            
            # 使用ChineseResumeParser解析
            result = self.parser.parse(content)
            
            return {
                "name": result.get("name", ""),
                "email": result["contact"].get("emails", [""])[0],
                "phone": result["contact"].get("phones", [""])[0],
                "skills": result.get("skills", []),
                "education": [edu["institution"] for edu in result.get("education", [])],
                "experience": [exp["company"] for exp in result.get("experience", [])]
            }
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    async def _read_file_content(self, file_path: str) -> str:
        """根据文件类型读取内容"""
        if file_path.endswith('.pdf'):
            from pdfminer.high_level import extract_text
            return extract_text(file_path)
        elif file_path.endswith('.docx'):
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
