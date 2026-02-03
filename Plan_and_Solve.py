import os 
import ast
from base_agent import HelloAgentsLLM
from dotenv import load_dotenv
from typing import List, Dict

try:
    load_dotenv()
except FileNotFoundError:
    print("警告：未找到.env文件，将使用系统环境变量")
except Exception as e:
    print(f"警告：加载.env文件时出错：{e}")

"""
      ——————  Part 1 : 规划器 (Planner) 生成清晰的行动蓝图，以列表形式 ———————
"""
PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家，你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个python列表，其中每个元素都是一个描述子任务的字符串。

问题：{question}

请严格按照以下格式输出你的计划，```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        
        # 为了生成计划，构建一个简单的消息列表
        messages = [{"role": "user", "content": prompt}]

        print(" --- 正在生成计划 --- ")
        # 使用流式输出来获取完整计划 
        response_text = self.llm_client.think(messages=messages)

        print(f"计划已经生成：\n {response_text}")

        # 解析LLM输出的列表字符串
        try:
            # 找到```python和```之间的内容
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # 使用ast.literal_eval来安全的执行字符串，将其转换为python列表
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []   
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"解析计划时出错：{e}")
            print(f"原始响应：{response_text}")
            return []
        except Exception as e:
            print(f"未知错误：{e}")
            return []


"""
      ——————  Part 2 : 执行器 (Executor) 逐一完成计划中的任务 ———————
                    1. 调用LLM去解决每一个子问题
                    2. 状态管理：记录每一步的执行结果，将其作为上下文提供给后续步骤
"""
EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对“当前步骤”的回答:
"""

class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        history = ""
        final_answer = ""
        
        print("\n--- 正在执行计划 ---")
        for i, step in enumerate(plan, 1):
            print(f"\n-> 正在执行步骤 {i}/{len(plan)}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question, plan=plan, history=history if history else "无", current_step=step
            )
            messages = [{"role": "user", "content": prompt}]
            
            response_text = self.llm_client.think(messages=messages) or ""
            
            history += f"步骤 {i}: {step}\n结果: {response_text}\n\n"
            final_answer = response_text
            print(f"✅ 步骤 {i} 已完成，结果: {final_answer}")
            
        return final_answer

# --- 4. 智能体 (Agent) 整合 ---
class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question: str):
        print(f"\n--- 开始处理问题 ---\n问题: {question}")
        plan = self.planner.plan(question)
        if not plan:
            print("\n--- 任务终止 --- \n无法生成有效的行动计划。")
            return
        final_answer = self.executor.execute(question, plan)
        print(f"\n--- 任务完成 ---\n最终答案: {final_answer}")

"""
      ——————  Part 3 : main() ———————

"""
if __name__ == '__main__':
    try:
        llm_client = HelloAgentsLLM()
        agent = PlanAndSolveAgent(llm_client)
        question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
        agent.run(question)
    except ValueError as e:
        print(e)














