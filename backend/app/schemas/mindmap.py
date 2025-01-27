from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class Relationship(BaseModel):
    source: str
    target: str
    type: str

class MindMapNode(BaseModel):
    id: str
    label: str
    children: List['MindMapNode'] = []
    relationships: Optional[List[Relationship]] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "label": "主题",
                "children": [
                    {
                        "id": "1-1",
                        "label": "子主题1",
                        "children": []
                    }
                ]
            }
        }

class MindMapRequest(BaseModel):
    content: str
    options: Dict = Field(default_factory=dict)

class MindMapResponse(BaseModel):
    success: bool = True
    data: Optional[str] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": "# 核心主题\n\n## 主要分类1\n### 内容1.1\n### 内容1.2\n",
                "error": None
            }
        }

class DocumentType(str, Enum):
    TEXT = "text"
    PDF = "pdf"

class DocumentAnalysisRequest(BaseModel):
    content: str = Field(..., description="文本内容或base64编码的PDF")
    doc_type: DocumentType
    max_depth: Optional[int] = Field(default=3, ge=1, le=5)
    title: Optional[str] = None 