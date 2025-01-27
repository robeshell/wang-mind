from app.core.mindmap.chains import MindMapChain
from app.schemas.mindmap import MindMapRequest, DocumentType, DocumentAnalysisRequest
from app.utils.logger import get_logger
import hashlib
import html
from app.utils.cache import cache
import asyncio
from typing import Optional, Callable, Awaitable, AsyncGenerator
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..document.pdf_parser import PDFParser
from app.core.mindmap.prompts import MindMapPrompts
from app.config.settings import settings
from fastapi import UploadFile
from app.core.models.llm import get_llm
from langchain.prompts import PromptTemplate

logger = get_logger()

class MindMapProcessor:
    def __init__(self, llm=None):
        if llm is None:
            llm = get_llm(temperature=settings.TEMPERATURE_MINDMAP)
        self.llm = llm
        
        # 配置文本分块器 - 增大 chunk_size，减少分块数
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=8000,  # 增大块大小
            chunk_overlap=500,  # 适当增加重叠以保持上下文
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？"]  # 减少分隔符，避免过度分块
        )
        self.chain = MindMapChain(llm=self.llm)
    
    async def generate(self, request: MindMapRequest) -> str:
        """生成思维导图的 markdown 文本"""
        try:
            text = request.content
            if len(text) > 8000:  # 只有长文本才进行分块
                # 1. 文本分块
                chunks = self.text_splitter.split_text(text)
                
                # 2. 直接让大模型处理主要观点
                main_points_prompt = PromptTemplate(
                    template=MindMapPrompts.get_main_points_template(),
                    input_variables=["text"]
                )
                formatted_prompt = main_points_prompt.format(
                    text="\n".join(chunks[:3])  # 只用前几个块来获取主要观点
                )
                response = await self.llm.ainvoke(formatted_prompt)
                main_points = str(response.content)
                
                # 3. 基于主要观点组织其他内容
                mindmap_prompt = PromptTemplate(
                    template=MindMapPrompts.get_mindmap_with_points_template(),
                    input_variables=["main_points", "details"]
                )
                formatted_prompt = mindmap_prompt.format(
                    main_points=main_points,
                    details="\n".join(chunks)
                )
            else:
                # 短文本直接生成
                mindmap_prompt = PromptTemplate(
                    template=MindMapPrompts.get_mindmap_template(),
                    input_variables=["text"]
                )
                formatted_prompt = mindmap_prompt.format(text=text)
            
            # 4. 生成最终思维导图
            response = await self.llm.ainvoke(formatted_prompt)
            return str(response.content)
            
        except Exception as e:
            logger.error(f"生成思维导图失败: {str(e)}")
            raise ValueError(f"生成思维导图失败: {str(e)}")

    def _validate_node_format(self, node: dict) -> dict:
        """验证并修复节点格式"""
        if not isinstance(node, dict):
            return {"id": str(hash(str(node))), "label": str(node), "children": []}
        
        if "children" in node:
            node["children"] = [
                self._validate_node_format(child) 
                for child in node["children"]
            ]
        
        if "id" not in node:
            node["id"] = str(hash(node.get("label", "")))
        
        return node

    def _extract_concepts(self, mindmap: dict) -> list:
        concepts = []
        self._extract_concepts_recursive(mindmap, concepts)
        return concepts

    def _extract_concepts_recursive(self, node: dict, concepts: list):
        if isinstance(node, dict) and "label" in node:
            concepts.append(node["label"])
        if isinstance(node, dict) and "children" in node:
            for child in node["children"]:
                self._extract_concepts_recursive(child, concepts)

    async def process_document(
        self, 
        request: DocumentAnalysisRequest,
        progress_callback: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> dict:
        """处理文档并生成思维导图"""
        try:
            if progress_callback:
                await progress_callback("开始解析文档...")
            
            # 1. 获取文本内容
            if request.doc_type == DocumentType.PDF:
                text = PDFParser.parse_base64_pdf(request.content)
                if progress_callback:
                    await progress_callback("PDF 解析完成")
            else:
                text = request.content
            
            if progress_callback:
                await progress_callback("开始分析文本...")
            
            # 2. 分割文本
            chunks = self.text_splitter.split_text(text)
            
            if progress_callback:
                await progress_callback(f"文本已分割为 {len(chunks)} 个块")
            
            # 3. 生成每个块的小结
            summaries = []
            for i, chunk in enumerate(chunks, 1):
                if progress_callback:
                    await progress_callback(f"正在处理第 {i}/{len(chunks)} 个文本块")
                summary = await self._generate_chunk_summary(chunk)
                summaries.append(summary)
                if progress_callback:
                    await progress_callback(f"第 {i}/{len(chunks)} 个文本块处理完成")
            
            if progress_callback:
                await progress_callback("所有文本块处理完成，开始生成思维导图...")
            
            # 4. 合并小结生成最终的思维导图
            combined_text = "\n".join(summaries)
            mindmap = await self._generate_mindmap(
                combined_text, 
                max_depth=request.max_depth,
                title=request.title
            )
            
            if progress_callback:
                await progress_callback("思维导图生成完成")
            
            return mindmap
            
        except Exception as e:
            logger.error(f"处理文档失败: {str(e)}")
            if progress_callback:
                await progress_callback(f"处理失败: {str(e)}")
            return {
                "id": "root",
                "label": "处理失败",
                "children": []
            }

    async def _generate_chunk_summary(self, text: str) -> str:
        """生成文本块的摘要"""
        try:
            response = await self.chain.process_text(text, is_summary=True)
            return response
        except Exception as e:
            logger.error(f"生成文本块摘要失败: {str(e)}")
            return text[:200] + "..."  # 降级处理

    async def _generate_mindmap(self, text: str, max_depth: int, title: Optional[str]) -> dict:
        """生成思维导图"""
        try:
            mindmap = await self.chain.process_text(
                text,
                is_summary=False  # 生成思维导图
            )
            
            # 验证并修复格式
            validated_mindmap = self._validate_node_format({
                "id": "root",
                "label": title or mindmap.get("topic", "主题"),
                "children": mindmap.get("children", [])
            })
            
            return validated_mindmap
            
        except Exception as e:
            logger.error(f"生成思维导图失败: {str(e)}")
            return {
                "id": "root",
                "label": title or "处理失败",
                "children": []
            } 

    async def process_document_with_progress(
        self, 
        request: DocumentAnalysisRequest,
        progress_callback: Optional[Callable[[str], Awaitable[str]]] = None
    ) -> AsyncGenerator[str, None]:
        """处理文档并生成思维导图，返回进度消息流"""
        try:
            if progress_callback:
                yield await progress_callback("开始解析文档...")
            
            # 1. 获取文本内容
            if request.doc_type == DocumentType.PDF:
                text = PDFParser.parse_base64_pdf(request.content)
                if progress_callback:
                    yield await progress_callback("PDF 解析完成")
            else:
                text = request.content
            
            # 2. 先分析文档结构
            structure = await self._analyze_document_structure(text)
            
            # 3. 初始化思维导图（使用文档结构）
            mindmap = {
                "id": "root",
                "label": request.title or "文档分析",
                "children": [
                    {
                        "id": f"section-{i}",
                        "label": section["title"],
                        "children": []
                    }
                    for i, section in enumerate(structure["sections"])
                ]
            }
            
            # 发送初始结构
            yield "data: " + json.dumps({
                "type": "update",
                "data": mindmap
            }) + "\n\n"
            
            # 4. 逐节处理文档内容
            for i, section in enumerate(structure["sections"]):
                if progress_callback:
                    yield await progress_callback(f"正在分析 {section['title']}...")
                
                try:
                    # 处理当前节的内容
                    section_map = await self._process_section(
                        section["content"],
                        section["type"]
                    )
                    
                    # 更新对应节点
                    for node in mindmap["children"]:
                        if node["id"] == f"section-{i}":
                            node["children"] = section_map["children"]
                            break
                    
                    # 发送更新
                    yield "data: " + json.dumps({
                        "type": "update",
                        "data": mindmap
                    }) + "\n\n"
                    
                except Exception as e:
                    logger.error(f"处理节 {section['title']} 失败: {str(e)}")
                    continue
            
            # 5. 最终优化
            try:
                optimized_map = await self._optimize_mindmap(mindmap)
                yield "data: " + json.dumps({
                    "type": "complete",
                    "data": optimized_map
                }) + "\n\n"
            except Exception as e:
                logger.error(f"优化失败: {str(e)}")
                yield "data: " + json.dumps({
                    "type": "complete",
                    "data": mindmap
                }) + "\n\n"
            
        except Exception as e:
            logger.error(f"处理失败: {str(e)}")
            yield "data: " + json.dumps({
                "type": "error",
                "data": str(e)
            }) + "\n\n"

    async def _analyze_document_structure(self, text: str) -> dict:
        """分析文档结构"""
        try:
            response = await self.llm.ainvoke(
                MindMapPrompts.DOCUMENT_STRUCTURE_TEMPLATE.format(text=text)  # 移除 temperature 参数
            )
            structure = json.loads(response)
            return structure
        except Exception as e:
            logger.error(f"分析文档结构失败: {str(e)}")
            return {
                "sections": [
                    {
                        "title": "文档内容",
                        "type": "content",
                        "content": text,
                        "importance": 3
                    }
                ]
            }

    async def _process_section(self, content: str, section_type: str) -> dict:
        """处理单个章节"""
        try:
            template = MindMapPrompts.get_section_template(section_type)
            response = await self.llm.ainvoke(
                template.format(text=content)  # 移除 temperature 参数
            )
            result = json.loads(response)
            return {
                "id": section_type,
                "label": self._get_section_label(section_type),
                "children": result["points"]
            }
        except Exception as e:
            logger.error(f"处理{section_type}部分失败: {str(e)}")
            return {
                "id": section_type,
                "label": self._get_section_label(section_type),
                "children": []
            }

    def _get_section_label(self, section_type: str) -> str:
        """获取章节标签"""
        labels = {
            "abstract": "摘要",
            "introduction": "引言",
            "method": "方法",
            "result": "结果",
            "conclusion": "结论",
            "general": "内容"
        }
        return labels.get(section_type, "内容")

    async def _optimize_mindmap(self, mindmap: dict) -> dict:
        """优化思维导图结构"""
        try:
            # 1. 去重
            seen_labels = set()
            optimized_children = []
            
            for node in mindmap["children"]:
                if node["label"] not in seen_labels:
                    seen_labels.add(node["label"])
                    optimized_children.append(node)
            
            mindmap["children"] = optimized_children
            
            # 2. 限制深度
            def limit_depth(node: dict, current_depth: int, max_depth: int):
                if current_depth >= max_depth:
                    node["children"] = []
                    return
                for child in node["children"]:
                    limit_depth(child, current_depth + 1, max_depth)
            
            limit_depth(mindmap, 0, 3)  # 限制最大深度为3
            
            return mindmap
        except Exception as e:
            logger.error(f"优化思维导图失败: {str(e)}")
            return mindmap

    async def process_document_stream(self, request: DocumentAnalysisRequest):
        """处理文档并生成思维导图（流式响应）"""
        try:
            # 1. 解析文档
            if request.doc_type == DocumentType.PDF:
                text = PDFParser.parse_base64_pdf(request.content)
                yield f"data: {json.dumps({'type': 'progress', 'message': 'PDF解析完成'})}\n\n"
            else:
                text = request.content

            if len(text) > 8000:  # 只有长文本才进行分块
                # 2. 文本分块
                chunks = self.text_splitter.split_text(text)
                total_chunks = len(chunks)
                
                # 3. 提取主要观点
                main_points_prompt = PromptTemplate(
                    template=MindMapPrompts.get_main_points_template(),
                    input_variables=["text"]
                )
                formatted_prompt = main_points_prompt.format(
                    text="\n".join(chunks[:3])  # 只用前几个块来获取主要观点
                )
                response = await self.llm.ainvoke(formatted_prompt)
                main_points = str(response.content)
                
                yield f"data: {json.dumps({'type': 'progress', 'message': '主要观点提取完成', 'current': 1, 'total': 2})}\n\n"

                # 4. 基于主要观点生成思维导图
                mindmap_prompt = PromptTemplate(
                    template=MindMapPrompts.get_mindmap_with_points_template(),
                    input_variables=["main_points", "details"]
                )
                formatted_prompt = mindmap_prompt.format(
                    main_points=main_points,
                    details="\n".join(chunks)
                )
            else:
                # 短文本直接生成
                mindmap_prompt = PromptTemplate(
                    template=MindMapPrompts.get_mindmap_template(),
                    input_variables=["text"]
                )
                formatted_prompt = mindmap_prompt.format(text=text)

            # 5. 生成最终思维导图
            response = await self.llm.ainvoke(formatted_prompt)
            
            # 6. 返回结果
            yield f"data: {json.dumps({'type': 'complete', 'data': str(response.content)})}\n\n"

        except Exception as e:
            logger.error(f"处理失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    def _create_sse_message(self, type: str, data: dict) -> str:
        """创建 SSE 消息"""
        return "data: " + json.dumps({
            "type": type,
            **data
        }) + "\n\n" 