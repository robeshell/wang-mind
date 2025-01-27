from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.models.llm import get_llm
from app.core.mindmap.prompts import MindMapPrompts
from app.utils.logger import get_logger
from app.utils.cache import cache
from app.config import settings
import json
import asyncio
from typing import Dict, List
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

logger = get_logger()

class MindMapChain:
    def __init__(self, llm=None):
        """初始化思维导图生成链"""
        self.llm = llm or get_llm()
        
        # 使用默认值，避免配置缺失时的错误
        chunk_size = getattr(settings, 'CHUNK_SIZE', 3000)
        chunk_overlap = getattr(settings, 'CHUNK_OVERLAP', 200)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )

        # 定义输出格式
        self.mindmap_response_schemas = [
            ResponseSchema(
                name="id",
                description="节点的唯一标识符",
                type="string"
            ),
            ResponseSchema(
                name="label",
                description="节点的显示文本",
                type="string"
            ),
            ResponseSchema(
                name="children",
                description="子节点数组",
                type="array"
            )
        ]
        
        self.details_response_schemas = [
            ResponseSchema(
                name="children",
                description="包含2-4个要点的数组，每个要点都有id和label字段",
                type="array"
            )
        ]
        
        self.mindmap_parser = StructuredOutputParser.from_response_schemas(self.mindmap_response_schemas)
        self.details_parser = StructuredOutputParser.from_response_schemas(self.details_response_schemas)

    async def process_text(self, text: str, is_summary: bool = False) -> dict:
        """处理文本并生成思维导图"""
        try:
            cache_key = f"mindmap:{hash(text)}"
            if cached := cache.get(cache_key):
                return cached

            mindmap = (
                await self._generate_mindmap(text[:3000]) if is_summary or len(text) <= 3000
                else await self._process_long_text(text)
            )

            cache.set(cache_key, mindmap)
            return mindmap

        except Exception as e:
            logger.error(f"生成思维导图失败: {str(e)}")
            return self._get_error_response("生成失败")

    async def _process_long_text(self, text: str) -> dict:
        """处理长文本"""
        try:
            chunks = self._split_text(text)
            summaries = await self._generate_chunk_summaries(chunks)
            structure = await self._generate_global_structure(summaries)
            return await self._fill_details(structure, chunks)
        except Exception as e:
            logger.error(f"处理长文本失败: {str(e)}")
            return self._get_error_response("处理失败")

    async def _generate_mindmap(self, text: str) -> dict:
        """生成简单的思维导图"""
        try:
            format_instructions = self.mindmap_parser.get_format_instructions()
            response = await self.llm.ainvoke(
                PromptTemplate(
                    template=MindMapPrompts.get_mindmap_template() + "\n{format_instructions}",
                    input_variables=["text"],
                    partial_variables={"format_instructions": format_instructions}
                ).format(text=text)
            )
            return self._validate_node_format(self.mindmap_parser.parse(response.content))
        except Exception as e:
            logger.error(f"生成思维导图失败: {str(e)}")
            return self._get_error_response("生成失败")

    async def _generate_chunk_summaries(self, chunks: List[str]) -> List[str]:
        """为每个文本块生成总结"""
        try:
            tasks = [
                self.llm.ainvoke(
                    PromptTemplate(
                        template=MindMapPrompts.get_chunk_summary_template(),
                        input_variables=["text"]
                    ).format(text=chunk)
                )
                for chunk in chunks
            ]
            responses = await asyncio.gather(*tasks)
            return [resp.content for resp in responses]
        except Exception as e:
            logger.error(f"生成块总结失败: {str(e)}")
            return []

    async def _generate_global_structure(self, summaries: List[str]) -> dict:
        """生成全局结构"""
        try:
            response = await self.llm.ainvoke(
                PromptTemplate(
                    template=MindMapPrompts.get_structure_template(),
                    input_variables=["text"]
                ).format(text="\n\n".join(summaries))
            )
            return self._validate_node_format(json.loads(response.content))
        except Exception as e:
            logger.error(f"生成全局结构失败: {str(e)}")
            return self._get_error_response("结构生成失败")

    async def _fill_details(self, structure: dict, chunks: List[str]) -> dict:
        """填充结构细节"""
        try:
            text = "\n\n".join(chunks)
            format_instructions = self.details_parser.get_format_instructions()
            
            for node in structure.get("children", []):
                try:
                    response = await self.llm.ainvoke(
                        PromptTemplate(
                            template=MindMapPrompts.get_details_template() + "\n{format_instructions}",
                            input_variables=["text", "topic", "category"],
                            partial_variables={"format_instructions": format_instructions}
                        ).format(
                            text=text,
                            topic=structure["label"],
                            category=node["label"]
                        )
                    )
                    details = self.details_parser.parse(response.content)
                    node["children"] = details.get("children", [])
                except Exception:
                    node["children"] = []
            return structure
        except Exception as e:
            logger.error(f"填充细节失败: {str(e)}")
            return structure

    def _split_text(self, text: str) -> List[str]:
        """分割文本"""
        if len(text) <= 3000:
            return [text]
        chunks = self.text_splitter.split_text(text)
        return self._merge_small_chunks(chunks)

    def _merge_small_chunks(self, chunks: List[str], min_size: int = 1000) -> List[str]:
        """合并小文本块"""
        if not chunks:
            return chunks
        merged = []
        current = chunks[0]
        for chunk in chunks[1:]:
            if len(current) + len(chunk) < min_size:
                current += "\n" + chunk
            else:
                merged.append(current)
                current = chunk
        merged.append(current)
        return merged

    def _validate_node_format(self, node: dict) -> dict:
        """验证节点格式"""
        if not isinstance(node, dict):
            return self._get_error_response(str(node))
        
        node.setdefault("label", "未知节点")
        node.setdefault("id", "root")
        node.setdefault("children", [])
        
        node["children"] = [
            self._validate_node_format(child) 
            for child in node["children"]
        ]
        return node

    def _get_error_response(self, message: str) -> dict:
        """生成错误响应"""
        return {
            "id": "root",
            "label": message,
            "children": []
        } 