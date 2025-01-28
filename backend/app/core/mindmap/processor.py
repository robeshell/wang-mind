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
import time

logger = get_logger()

class MindMapProcessor:
    def __init__(self, llm=None):
        if llm is None:
            llm = get_llm(
                temperature=settings.LLM_TEMPERATURE,
                presence_penalty=settings.LLM_PRESENCE_PENALTY,
                frequency_penalty=settings.LLM_FREQUENCY_PENALTY,
                top_p=settings.LLM_TOP_P,
                max_tokens=settings.LLM_MAX_TOKENS
            )
        self.llm = llm
        
        # 调整分块大小和重叠度
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=12000,  # 增加块大小
            chunk_overlap=200,  # 减少重叠以降低重复处理
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，"]  # 优化分隔符
        )
        self.chain = MindMapChain(llm=self.llm)
        
        # 增加并发限制和缓存配置
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self.chunk_cache = {}
    
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
            try:
                # 调用大模型（添加超时控制）
                async with asyncio.timeout(30):  # 30秒超时
                    response = await self.llm.ainvoke(formatted_prompt)
                result = str(response.content)
            except asyncio.TimeoutError:
                logger.error("大模型响应超时")
                raise Exception("思维导图生成超时，请重试")
            return result
            
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
        try:
            # 获取文本内容
            text = PDFParser.parse_base64_pdf(request.content) if request.doc_type == DocumentType.PDF else request.content
            
            # 计算缓存键
            cache_key = hashlib.md5(text[:1000].encode()).hexdigest()  # 只用前1000字符作为缓存键
            if cached_result := cache.get(cache_key):
                return cached_result

            # 文本分块
            chunks = self.text_splitter.split_text(text)
            total_chunks = len(chunks)
            
            if progress_callback:
                await progress_callback(f"文本已分割为 {total_chunks} 个块")

            # 批量处理文本块
            processed_chunks = []
            batch_size = settings.CHUNK_BATCH_SIZE
            for i in range(0, total_chunks, batch_size):
                batch = chunks[i:i + batch_size]
                tasks = [self._process_chunk_with_cache(chunk) for chunk in batch]
                batch_results = await asyncio.gather(*tasks)
                processed_chunks.extend(batch_results)
                
                if progress_callback:
                    await progress_callback(f"已处理 {min(i + batch_size, total_chunks)}/{total_chunks} 个文本块")

            # 合并处理结果
            combined_text = "\n".join(processed_chunks)
            mindmap = await self._generate_mindmap(
                combined_text,
                max_depth=request.max_depth,
                title=request.title
            )
            
            # 缓存结果
            try:
                cache.set(cache_key, mindmap, expire=3600)  # 使用 expire 参数
            except TypeError:
                logger.warning("缓存设置不支持过期时间参数")
                cache.set(cache_key, mindmap)
            return mindmap

        except Exception as e:
            logger.error(f"处理文档失败: {str(e)}")
            return {
                "id": "root",
                "label": "处理失败",
                "children": []
            }

    async def _process_chunk_with_cache(self, chunk: str) -> str:
        """使用缓存处理文本块"""
        chunk_key = hashlib.md5(chunk.encode()).hexdigest()
        if cached_result := self.chunk_cache.get(chunk_key):
            return cached_result

        async with self.semaphore:
            try:
                response = await self.llm.ainvoke(
                    MindMapPrompts.get_main_points_template().format(text=chunk)
                )
                result = str(response.content)
                self.chunk_cache[chunk_key] = result
                return result
            except Exception as e:
                logger.error(f"处理文本块失败: {str(e)}")
                return chunk[:200] + "..."  # 降级处理

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

    async def _process_chunk_with_semaphore(self, chunk: str) -> str:
        """使用信号量控制并发处理文本块"""
        async with self.semaphore:
            try:
                response = await self.llm.ainvoke(
                    MindMapPrompts.get_main_points_template().format(text=chunk)
                )
                return str(response.content)
            except Exception as e:
                logger.error(f"处理文本块失败: {str(e)}")
                return chunk[:200] + "..."  # 降级处理

    async def process_document_stream(self, request: DocumentAnalysisRequest):
        """处理文档并生成思维导图（流式响应）"""
        start_time = time.time()
        
        try:
            # 发送开始消息
            yield self._create_sse_message("start", {"message": "开始处理文档"})
            
            # 1. 解析文档
            parse_start = time.time()
            text = PDFParser.parse_base64_pdf(request.content) if request.doc_type == DocumentType.PDF else request.content
            parse_time = time.time() - parse_start
            logger.info(f"文档解析耗时: {parse_time:.2f}秒")
            yield self._create_sse_message("progress", {"message": f"PDF解析完成, 耗时{parse_time:.2f}秒"})

            # 2. 准备文本
            prep_start = time.time()
            if len(text) > settings.CHUNK_SIZE:
                # 取更多的内容进行处理
                main_content = text[:int(settings.CHUNK_SIZE * settings.TEXT_HEAD_RATIO)]
                
                # 提取关键段落
                important_paragraphs = []
                remaining_text = text[int(settings.CHUNK_SIZE * settings.TEXT_HEAD_RATIO):]
                paragraphs = remaining_text.split('\n\n')
                for para in paragraphs[:5]:  # 取剩余部分的前5个段落
                    if any(keyword in para.lower() for keyword in ['结果', '实验', '性能', '创新', '贡献']):
                        important_paragraphs.append(para)
                
                text_to_process = main_content + "\n\n重要补充：\n" + "\n".join(important_paragraphs)
            else:
                text_to_process = text
            prep_time = time.time() - prep_start
            logger.info(f"文本准备耗时: {prep_time:.2f}秒")

            # 3. 准备提示词
            gen_start = time.time()
            mindmap_prompt = PromptTemplate(
                template=MindMapPrompts.get_mindmap_template(),
                input_variables=["text"]
            )
            formatted_prompt = mindmap_prompt.format(text=text_to_process)
            
            # 4. 使用流式响应，并累积结果
            full_result = []
            reasoning_content = []  # 存储思维链内容
            content = []  # 存储最终回答
            buffer = []
            is_thinking = False  # 用于 DeepSeek 模型的思考标记

            messages = [
                ("human", formatted_prompt)
            ]

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
                elif "</think>" in chunk_content:  # 使用 </think> 作为思考过程的结束标记
                    is_thinking = False
                    chunk_content = chunk_content.replace("</think>", "")
                    if chunk_content.strip():  # 如果还有其他内容
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

            # 合并完整结果
            final_result = "".join(content)
            final_reasoning = "".join(reasoning_content)
            gen_time = float(time.time() - gen_start)
            logger.info(f"思维导图生成耗时: {gen_time:.2f}秒")
            yield self._create_sse_message("progress", {"message": f"思维导图生成完成, 耗时{gen_time:.2f}秒"})

            # 5. 计算总耗时
            total_time = float(time.time() - start_time)
            logger.info(f"总处理耗时: {total_time:.2f}秒")
            
            # 6. 返回最终结果
            yield self._create_sse_message("complete", {
                "data": final_result,
                "reasoning": final_reasoning,  # 添加思维链内容
                "timing": {
                    "parse": float(round(parse_time, 2)),
                    "preparation": float(round(prep_time, 2)),
                    "generation": float(round(gen_time, 2)),
                    "total": float(round(total_time, 2))
                }
            })

        except Exception as e:
            error_time = float(time.time() - start_time)
            logger.error(f"处理失败: {str(e)}, 耗时: {error_time:.2f}秒")
            yield self._create_sse_message("error", {
                "message": str(e),
                "timing": {
                    "error_time": float(round(error_time, 2))
                }
            })

    def _create_sse_message(self, type: str, data: dict) -> str:
        """创建 SSE 消息"""
        message = {"type": type, **data}
        return f"data: {json.dumps(message)}\n\n"

    async def process_stream(self, content: str) -> AsyncGenerator[dict, None]:
        current_node = ""
        async for chunk in self._generate_mindmap(content):
            if isinstance(chunk, dict):  # 处理进度信息
                yield {
                    "type": "progress",
                    "progress": chunk.get("progress", 0),
                    "message": chunk.get("message", "")
                }
                continue

            current_node += chunk
            # 检查是否是一个完整的节点（以换行符结尾）
            if "\n" in current_node:
                lines = current_node.split("\n")
                # 保留最后一个不完整的行
                complete_lines = lines[:-1]
                current_node = lines[-1]
                
                if complete_lines:
                    yield {
                        "type": "generating",
                        "partial": "\n".join(complete_lines) + "\n"
                    }

        # 发送最后剩余的内容
        if current_node.strip():
            yield {
                "type": "generating",
                "partial": current_node + "\n"
            }

        # 发送完整结果
        yield {
            "type": "complete",
            "data": self.result
        }

    async def process_text(self, request: MindMapRequest) -> dict:
        """处理文本并生成思维导图"""
        try:
            # 1. 准备提示词
            mindmap_prompt = PromptTemplate(
                template=MindMapPrompts.get_mindmap_template(),
                input_variables=["text"]
            )
            formatted_prompt = mindmap_prompt.format(text=request.content)
            
            # 2. 使用流式响应
            full_result = []
            reasoning_content = []
            content = []
            buffer = []
            is_thinking = False

            messages = [
                ("human", formatted_prompt)
            ]

            async for chunk in self.llm.astream(messages):
                chunk_content = str(chunk.content)
                
                # 处理 OpenAI 的 reasoning_content
                if hasattr(chunk, 'additional_kwargs') and 'reasoning_content' in chunk.additional_kwargs:
                    reasoning_chunk = chunk.additional_kwargs['reasoning_content']
                    if reasoning_chunk:
                        reasoning_content.append(reasoning_chunk)
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
                    continue
                
                if is_thinking:
                    reasoning_content.append(chunk_content)
                else:
                    content.append(chunk_content)

            # 3. 合并结果
            final_result = "".join(content)
            final_reasoning = "".join(reasoning_content)

            # 4. 返回结果
            return {
                "data": final_result,
                "reasoning": final_reasoning
            }

        except Exception as e:
            logger.error(f"处理失败: {str(e)}")
            raise 

    async def process_text_stream(self, request: MindMapRequest):
        """处理文本并生成思维导图（流式响应）"""
        try:
            # 1. 发送开始消息
            yield self._create_sse_message("start", {"message": "开始处理文本"})
            
            # 2. 准备提示词
            mindmap_prompt = PromptTemplate(
                template=MindMapPrompts.get_mindmap_template(),
                input_variables=["text"]
            )
            formatted_prompt = mindmap_prompt.format(text=request.content)
            
            # 3. 使用流式响应
            full_result = []
            reasoning_content = []
            content = []
            buffer = []
            is_thinking = False

            messages = [
                ("human", formatted_prompt)
            ]

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

            # 4. 合并完整结果
            final_result = "".join(content)
            final_reasoning = "".join(reasoning_content)
            
            # 5. 返回最终结果
            yield self._create_sse_message("complete", {
                "data": final_result,
                "reasoning": final_reasoning
            })

        except Exception as e:
            logger.error(f"处理失败: {str(e)}")
            yield self._create_sse_message("error", {
                "message": str(e)
            }) 