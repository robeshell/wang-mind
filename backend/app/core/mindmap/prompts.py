from langchain.prompts import PromptTemplate
from typing import Dict, List

class MindMapPrompts:
    # 基础思维导图模板（用于短文本）
    MINDMAP_TEMPLATE = """
作为AI助手，请详细分析文本并生成一个内容丰富的思维导图。要求：

1. 使用 Markdown 格式，必须包含完整的三级结构：
   - 使用 # 作为一级标题（核心主题，需概括文章主要内容）
   - 使用 ## 作为二级标题（4-6个主要方面，每个方面需完整描述一个核心要点）
   - 使用 ### 作为三级标题（每个二级标题下3-5个具体要点，需包含细节和数据）
   - 使用 - 作为列表项（每个三级标题下2-3个补充说明，包含具体案例或数据）

2. 内容详实要求：
   - 一级标题：15-20字，需概括文章核心内容
   - 二级标题：20-30字，完整表达一个主要观点
   - 三级标题：30-40字，包含具体细节和关键数据
   - 列表项：40-50字，提供详细的解释、案例或数据支持

3. 内容质量要求：
   - 保持专业性：使用领域专业术语
   - 数据完整性：保留文中的具体数据和实验结果
   - 逻辑性：确保各级内容之间有清晰的逻辑关系
   - 重要性：突出创新点和关键技术特性
   - 完整性：涵盖文章所有重要内容

4. 结构示例：
# Transformer：基于自注意力机制的深度学习架构创新（核心主题）
## 技术创新：多头自注意力机制突破传统序列处理限制（主要方面）
### 自注意力计算：通过Query、Key、Value三矩阵实现全局依赖建模（具体要点）
- 使用点积注意力计算相似度，并通过softmax归一化得到注意力权重
- 引入缩放因子1/√dk防止梯度消失，确保训练稳定性
### 多头机制：8-12个注意力头并行计算，捕获多样化特征（具体要点）
- 每个头独立学习不同的特征表示，如语法、语义等关系
- 通过线性变换和拼接整合多头信息，增强模型表达能力
### 性能指标与实验结果（具体要点）
- 在WMT 2014英德翻译任务中达到28.4 BLEU，相比基线模型提升2.0分（具体数据）
- 训练时间仅需3.5天，使用8个P100 GPU，总计算量为3.3×10^18 FLOPs（硬件细节）

### 模型参数与配置（具体要点）
- 使用512维度的嵌入向量，2048维度的前馈网络，总参数量达到213M（架构细节）
- 采用Adam优化器，β1=0.9，β2=0.98，ε=10^-9，使用warmup_steps=4000（训练配置）

请基于以下文本生成完整且内容丰富的思维导图：
{text}
"""

    # 主要观点提取模板（用于长文本的第一步）
    MAIN_POINTS_TEMPLATE = """
用最简洁的方式列出文本的主要观点：
- 仅提取3个最重要的观点
- 每个观点不超过10字
- 直接列出要点，不要解释

文本内容：
{text}
"""

    # 基于主要观点的思维导图生成模板（用于长文本的第二步）
    MINDMAP_WITH_POINTS_TEMPLATE = """
基于以下主要观点和详细内容，生成一个简洁的思维导图结构。要求：
1. 使用 Markdown 格式
2. 最多3层结构
3. 每层节点不超过5个
4. 每个节点的描述尽量简短，不超过20字
5. 直接输出结果，无需解释

主要观点：
{main_points}

详细内容：
{details}
"""

    @staticmethod
    def get_mindmap_template() -> str:
        return MindMapPrompts.MINDMAP_TEMPLATE

    @staticmethod
    def get_main_points_template() -> str:
        return MindMapPrompts.MAIN_POINTS_TEMPLATE

    @staticmethod
    def get_mindmap_with_points_template() -> str:
        return MindMapPrompts.MINDMAP_WITH_POINTS_TEMPLATE