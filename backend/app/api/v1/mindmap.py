from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from ...schemas.mindmap import DocumentAnalysisRequest, MindMapRequest, MindMapResponse, DocumentType
from ...core.mindmap.processor import MindMapProcessor
from ...core.models.llm import get_llm
from app.utils.logger import get_logger
import asyncio
import json
import base64

router = APIRouter(prefix="/mindmap", tags=["mindmap"])

logger = get_logger()

@router.post("/from-text/stream")
async def create_mindmap_from_text(request: MindMapRequest):
    """从文本生成思维导图（流式响应）"""
    processor = MindMapProcessor(get_llm())
    
    return StreamingResponse(
        processor.process_text_stream(request),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@router.post("/from-document/stream")
async def create_mindmap_from_document(request: DocumentAnalysisRequest):
    """从文档生成思维导图（流式响应）"""
    processor = MindMapProcessor(get_llm())
    
    return StreamingResponse(
        processor.process_document_stream(request),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"} 