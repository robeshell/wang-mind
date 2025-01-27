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

@router.post("/generate", response_model=MindMapResponse)
async def generate_mindmap(request: MindMapRequest):
    """从文本生成思维导图（旧版本，建议使用 /from-text）"""
    logger.warning("使用了旧版 API，建议迁移到 /from-text")
    return await create_mindmap_from_text(request)

@router.post("/from-document", response_model=MindMapResponse)
async def create_mindmap_from_document(
    request: DocumentAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """从文档生成思维导图（旧版本，建议使用 /from-document/stream）"""
    logger.warning("使用了旧版 API，建议迁移到 /from-document/stream")
    processor = MindMapProcessor(get_llm())
    mindmap = await processor.process_document(request)
    return MindMapResponse(success=True, data=mindmap)

@router.post("/from-text")
async def create_mindmap_from_text(request: MindMapRequest) -> MindMapResponse:
    """从文本生成思维导图"""
    try:
        processor = MindMapProcessor(get_llm())
        markdown = await processor.generate(request)
        return MindMapResponse(
            success=True,
            data=markdown
        )
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-document/stream")
async def create_mindmap_from_document_stream(
    request: DocumentAnalysisRequest
) -> StreamingResponse:
    """从文档生成思维导图（流式响应）"""
    try:
        processor = MindMapProcessor(get_llm())
        return StreamingResponse(
            processor.process_document_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"处理文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/from-document/stream")
async def create_mindmap_from_document_stream_get(
    data: str = Query(..., description="JSON encoded request data")
) -> StreamingResponse:
    """从文档生成思维导图（GET 流式响应）"""
    try:
        # 解析请求数据
        request_data = json.loads(data)
        request = DocumentAnalysisRequest(**request_data)
        
        logger.info("初始化 LLM...")
        llm = get_llm()
        logger.info("LLM 初始化成功")
        
        processor = MindMapProcessor(llm)
        
        async def generate():
            try:
                async for message in processor.process_document_stream(request):
                    yield message
            except Exception as e:
                logger.error(f"处理文档失败: {str(e)}")
                yield f"data: {{'type': 'error', 'message': '{str(e)}'}}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"处理文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-pdf")
async def create_mindmap_from_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
) -> StreamingResponse:
    """从 PDF 文件生成思维导图"""
    try:
        logger.info(f"接收到 PDF 文件: {file.filename}")
        content = await file.read()
        base64_content = base64.b64encode(content).decode()
        
        request = DocumentAnalysisRequest(
            title=file.filename,
            content=base64_content,
            doc_type=DocumentType.PDF
        )
        
        return await create_mindmap_from_document_stream(request)
        
    except Exception as e:
        logger.error(f"处理 PDF 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        llm = get_llm()  # 测试 LLM 初始化
        return {"status": "healthy", "llm": "ok"}
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="服务不可用"
        ) 