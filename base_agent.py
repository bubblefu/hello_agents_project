import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

# 加载 .env 文件中的环境变量
load_dotenv()

class HelloAgentsLLM:
    """
    为本书 "Hello Agents" 定制的LLM客户端。
    它用于调用任何兼容OpenAI接口的服务，并默认使用流式响应。
    """
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")
        # 构建了self.client 即openai的客户端
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        think() ————向大语言模型发送消息并获取响应
        流程：
            1. 打印开始调用提示
            2. 创建流式 API 请求
            3. 迭代处理每个响应块
            4. 收集并返回完整响应
                4.1 实时显示：逐块显示生成内容
                4.2 内存高效：无需等待完整响应即可开始处理
                4.3 用户体验好：提供实时反馈
            5. 处理异常情况
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True, # stream 是 Generator，返回的每个chunk是 ChatCompletionChunk, 若为False,则为一次性完整输出
            )
            
            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            collected_content = []
             # 每次迭代获取一个数据块
            for chunk in response:  
                # 为什么需要 or ""？  ————有些 chunk 只包含 metadata（如 role、finish_reason），没有 content
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)    # O(1) 操作
            print()  # 在流式输出结束后换行
            return "".join(collected_content)        # 一次性拼接，O(n) 效率

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None         # 返回安全值而不是崩溃

# --- 客户端使用示例 ---
if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM()
        
        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "斯蒂芬霍金的物理学成就，简单说一下就行"}
        ]
        
        print("--- 调用LLM ---")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n--- 完整模型响应 ---")
            print(responseText)

    except ValueError as e:
        print(e)



