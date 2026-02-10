from typing import List, Dict, Any, Optional,Literal,TypedDict
from base_agent import HelloAgentsLLM
from log import logger
import json
"""
      ——————  Part 1 : Memory模块 ———————
            1. Reflection 的核心在于迭代，而迭代的前提是能够记住之前的尝试和获得的反馈。
            2. 一个“短期记忆”模块是实现该范式的必需品。这个记忆模块将负责存储每一次“执行-反思”循环的完整轨迹。
"""
RecordType = Literal["execution", "reflection"]
class Record(TypedDict):
    type:RecordType
    content: str

class Memory:
    """
    一个简单的短期记忆模块，用于存储智能体的行动与反思轨迹。
    """
    def __init__(self):
        # 初始化空列表来存储所有记录
        self.records: List[Record] = []

    def add_record(self, record_type: RecordType, content: str) -> None:
        """
        向记忆中添加一条新记录。

        参数:
        - record_type (RecordType): 记录的类型 ('execution' 或 'reflection'),用 Literal 限制
        - content (str): 记录的具体内容 (例如，生成的代码或反思的反馈)。
        """
        record = {"type": record_type, "content": content}
        self.records.append(record)
        logger.info("记忆已更新，增加一条'%s'记录", record_type)
    # 先保留get_trajectory function 
    def get_trajectory(self) -> str:
        """
        将所有记忆记录格式化为一个连贯的字符串文本，用于构建提示词。
        """
        trajectory_parts = []
        for record in self.records:
            if record['type'] == 'execution':
                trajectory_parts.append(f"--- 上一轮尝试 (代码) ---\n{record['content']}")
            elif record['type'] == 'reflection':
                trajectory_parts.append(f"--- 评审员反馈 ---\n{record['content']}")
        
        return "\n\n".join(trajectory_parts)

    def get_last_execution(self) -> Optional[str]:
        """
        获取最近一次的执行结果 (例如，最新生成的代码)。
        如果不存在，则返回 None。
        """
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None
"""
      ——————  Part 2 : Reflection Prompt Words ———————
            1. INITIAL_PROMPT_TEMPLATE ———— 智能体首次尝试解决问题的提示词，内容相对直接，只要求模型完成指定任务。
            2. REFLECT_PROMPT_TEMPLATE ———— Reflection 机制的灵魂。它指示模型扮演“代码评审员”的角色，对上一轮生成的代码进行批判性分析，并提供具体的、可操作的反馈。
            3. REFINE_PROMPT_TEMPLATE  ———— 收到反馈后，这个提示词将引导模型根据反馈内容，对原有代码进行修正和优化。
"""

INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。请根据以下要求,编写一个Python函数。
你的代码必须包含完整的函数签名、文档字符串,并遵循PEP 8编码规范。

要求：{task}

请直接输出代码，不要包含任何额外的解释。
"""

REFLECT_PROMPT_TEMPLATE = """
你是一位及其严格的代码评审专家和资深算法工程师，对代码的性能有极致要求。
你的任务是审查以下Python代码,并专注于找出其在算法效率上的主要瓶颈。

# 原始任务：
{task}

# 待审查的代码：
```python
{code}
```

请分析该代码的时间复杂度，并思考是否存在一种<strong>算法上更优</strong>的解决方案来显著提升性能。

请你严格按照以下 JSON 格式输出，不要包含任何多余文本，不要使用 Markdown，不要添加解释,请确保输出的 JSON 包含 "needs_improvement"、"analysis" 和 "suggestion" 三个字段。：
{{
"needs_improvement": true 或 false,
"analysis": "对当前算法复杂度的简要分析",
"suggestion": "如果 needs_improvement 为 true，给出明确的优化方向；否则填写 空字符串"
}}
"""

REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务：
{task}

# 你上一轮尝试的代码：
{last_code_attempt}

评审员的反馈：
{feedback}

请根据评审员的反馈，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串,并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
"""

class ReflectionAgent:
    def __init__(self, llm_client, max_iterations=3):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations
    
    def _get_llm_response(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        response_text = self.llm_client.think(messages=messages) or ""
        return response_text
    
    def run(self, task: str):
        # print(f"\n --- 开始处理任务 ---\n任务：{task}")
        logger.info("开始处理任务:%s", task)

        # ---1. 初始执行 ---
        logger.info("正在进行初始尝试")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution", initial_code)

        # ---2. 迭代循环：反思与优化 ---
        for i in range(self.max_iterations):
            logger.info("第 %d / %d 轮迭代",i+1, self.max_iterations)

            # a. 反思
            logger.info("正在进行反思")
            last_code = self.memory.get_last_execution()
            if last_code is None:
                logger.error("没有找到上一次的执行记录")
                break
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            
            # b. 检查是否需要停止
            try:
                data = json.loads(feedback)   # json.loads 输入JSON格式，返回python的格式类型，这里是字典
            except json.JSONDecodeError:
                logger.error("反思阶段JSON解析失败（第 %d 轮），内容为：%s", i+1, feedback[:200])
                break           
            #   b.1 提取反馈内容
            analysis = data["analysis"]
            suggestion = data["suggestion"]
            feedback_text = f"{analysis}\n{suggestion}".strip()
            self.memory.add_record("reflection", feedback_text)
            #   b.2 判断是否停止
            if not data.get("needs_improvement",True):        # 即使字段缺失，也不会崩
                logger.warning("反思认为代码已无需改进，任务提前结束")
                break

            # c. 优化
            logger.info("正在进行优化")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_code,
                feedback=feedback
            )
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", refined_code)
        
        final_code = self.memory.get_last_execution()
        logger.info("任务完成")
        logger.debug("最终生成的代码:\n%s", final_code)
        return final_code

if __name__ == '__main__':
    try:
        llm_client  = HelloAgentsLLM()
    except Exception as e:
        logger.error("初始化 LLM 客户端失败: %s", e)
        exit()
    
    agent = ReflectionAgent(llm_client, max_iterations=2)   

    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    agent.run(task)



"""
reflection 如何明确停止改进的条件？  reflection 本质是“决策控制问题”，不是 prompt 问题。

1. 外部evaluator
    写单元测试
    写规则校验
    用另一个模型评分
    用embedding similarity
2. 规则型停止
    达到最大轮数          ————客观却粗糙
    达到token上限         
    分数超过阈值
3. 模型自评型停止         ————半主观
    给当前方案打多少分，超过了就可以了。很多research agent用这个

"""


"""
注意：只有最外层的 `{` 和 `}` 被转义为 `{{` 和 `}}`，而 `{task}` 和 `{code}` 保持不变，因为它们是真正的 `.format()` 占位符。

- `{{` → 在最终字符串中变成 `{`
- `}}` → 在最终字符串中变成 `}`
- `{task}` → 被替换为实际任务内容
- `{code}` → 被替换为实际代码
"""