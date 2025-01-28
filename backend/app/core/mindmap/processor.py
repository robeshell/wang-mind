from app.schemas.mindmap import MindMapRequest, DocumentType, DocumentAnalysisRequest
from app.utils.logger import get_logger
import json
from ..document.pdf_parser import PDFParser
from app.core.mindmap.prompts import MindMapPrompts
from app.config.settings import settings
from langchain.prompts import PromptTemplate
import time

logger = get_logger()

class MindMapProcessor:
    def __init__(self, llm):
        self.llm = llm
    
    def _create_sse_message(self, type: str, data: dict) -> str:
        """创建 SSE 消息"""
        message = {"type": type, **data}
        return f"data: {json.dumps(message)}\n\n"

    async def _process_llm_stream(self, prompt: str):
        """处理 LLM 流式响应的核心逻辑"""
        try:
            # 1. 发送开始消息
            yield self._create_sse_message("start", {"message": "开始处理"})
            
            # 2. 使用流式响应
            reasoning_content = []
            content = []
            buffer = []
            is_thinking = False

            messages = [("human", prompt)]
            start_time = time.time()

            async for chunk in self.llm.astream(messages):
                chunk_content = str(chunk.content)
                
                # 处理 OpenAI 的 reasoning_content
                if hasattr(chunk, 'additional_kwargs') and 'reasoning_content' in chunk.additional_kwargs:
                    reasoning_chunk = chunk.additional_kwargs['reasoning_content']
                    if reasoning_chunk:
                        reasoning_content.append(reasoning_chunk)
                        yield self._create_sse_message("reasoning", {
                            "partial": reasoning_chunk
                        })
                        continue
                
                # 处理 DeepSeek 的 <think> 标记
                if "<think>" in chunk_content:
                    is_thinking = True
                    chunk_content = chunk_content.replace("<think>", "")
                elif "</think>" in chunk_content:
                    is_thinking = False
                    chunk_content = chunk_content.replace("</think>", "")
                    if chunk_content.strip():
                        reasoning_content.append(chunk_content)
                        yield self._create_sse_message("reasoning", {
                            "partial": chunk_content
                        })
                    continue
                
                if is_thinking:
                    reasoning_content.append(chunk_content)
                    yield self._create_sse_message("reasoning", {
                        "partial": chunk_content
                    })
                else:
                    content.append(chunk_content)
                    buffer.append(chunk_content)
                    
                    # 每累积10个字符就发送一次
                    if len(''.join(buffer)) >= 10:
                        yield self._create_sse_message("generating", {"partial": ''.join(buffer)})
                        buffer = []

            # 3. 合并结果
            final_result = "".join(content)
            final_reasoning = "".join(reasoning_content)
            total_time = float(time.time() - start_time)
            
            # 4. 返回最终结果
            yield self._create_sse_message("complete", {
                "data": final_result,
                "reasoning": final_reasoning,
                "timing": {
                    "total": float(round(total_time, 2))
                }
            })

        except Exception as e:
            logger.error(f"处理失败: {str(e)}")
            yield self._create_sse_message("error", {
                "message": str(e)
            })

    async def process_text_stream(self, request: MindMapRequest):
        """处理文本并生成思维导图（流式响应）"""
        prompt = PromptTemplate(
            template=MindMapPrompts.get_mindmap_template(),
            input_variables=["text"]
        ).format(text=request.content)
        
        async for message in self._process_llm_stream(prompt):
            yield message

    async def process_document_stream(self, request: DocumentAnalysisRequest):
        """处理文档并生成思维导图（流式响应）"""
        try:
            # 1. 解析文档
            text = PDFParser.parse_base64_pdf(request.content) if request.doc_type == DocumentType.PDF else request.content
            
            # 2. 准备文本
            if len(text) > settings.CHUNK_SIZE:
                main_content = text[:int(settings.CHUNK_SIZE * settings.TEXT_HEAD_RATIO)]
                important_paragraphs = []
                remaining_text = text[int(settings.CHUNK_SIZE * settings.TEXT_HEAD_RATIO):]
                paragraphs = remaining_text.split('\n\n')
                for para in paragraphs[:5]:
                    if any(keyword in para.lower() for keyword in ['结果', '实验', '性能', '创新', '贡献']):
                        important_paragraphs.append(para)
                
                text_to_process = main_content + "\n\n重要补充：\n" + "\n".join(important_paragraphs)
            else:
                text_to_process = text

            # 3. 生成思维导图
            prompt = PromptTemplate(
                template=MindMapPrompts.get_mindmap_template(),
                input_variables=["text"]
            ).format(text=text_to_process)
            
            async for message in self._process_llm_stream(prompt):
                yield message

        except Exception as e:
            logger.error(f"处理文档失败: {str(e)}")
            yield self._create_sse_message("error", {
                "message": str(e)
            })