# 多平台支持

import os
from log import logger
from typing import Optional
from openai import OpenAI   
from core.llm import HelloAgentsLLM

class MyLLM(HelloAgentsLLM):
    """
    一个自定义的LLM客户端，通过继承增加了对ModelScope的支持
    """
    def __init__(
            self, 
            model: Optional[str] = None,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            provider: Optional[str] = "auto",
            **kwargs
    ):
        if provider == "modelscope":
            logger.info("正在使用自定义的 ModelScope Provider")
            self.provider = "modelscope"

            # 解析 MS 的凭证
            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY")
            self.base_url = base_url or os.getenv("MODELSCOPE_URL")

            # 验证凭证
            if not api_key:
                raise ValueError("ModelScope API key not found.")
            
            # 设置默认模型和其他参数
            self.model = model or os.getenv("LLM_MODEL_ID") or "Qwen/Qwen2.5-VL-72B-Instruct"
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens')
            self.timeout = kwargs.get('timeout', 60)

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

        else:
            super().__init__(model=model, api_key=api_key, base_url=base_url, provider=provider, **kwargs)
