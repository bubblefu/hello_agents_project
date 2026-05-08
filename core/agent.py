"""构建Agent基类，通过abstract base classes模块实现它（abc）"""

from abc import ABC
from typing import Optional, Any
from core.message import Message
from core.config import Config
from core.llm import HelloAgentsLLM

class Agent(ABC):
    """Agent基类"""

    def __init__(
            self,
            name: str,
            llm: HelloAgentsLLM,
            system_prompt: Optional[str] = None,
            config: Optional[Config] = None
    ):
        self.name = name 
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self._history: list[Message] = []

    @classmethod
    def run(self, input_text: str, **kwargs) -> str:
        """运行agent"""
        pass

    def add_message(self, message: Message):
        """添加消息到历史记录"""
        self._history.append(message)

    def clear_history(self):
        self._history.clear()

    def get_history(self) -> list[Message]:
        return self._history.copy()
    
    def __str__(self) -> str:
        return f"Agent(name={self.name}, provider={self.llm.provider})"