import base64
import io
from PyPDF2 import PdfReader
from typing import Optional

class PDFParser:
    @staticmethod
    def parse_base64_pdf(base64_string: str) -> str:
        """将 base64 编码的 PDF 转换为文本"""
        try:
            # 解码 base64 字符串
            pdf_bytes = base64.b64decode(base64_string)
            pdf_file = io.BytesIO(pdf_bytes)
            
            # 读取 PDF
            reader = PdfReader(pdf_file)
            text = ""
            
            # 提取所有页面的文本
            for page in reader.pages:
                text += page.extract_text() + "\n"
                
            return text.strip()
        except Exception as e:
            raise ValueError(f"PDF parsing failed: {str(e)}") 