from typing import Optional, Iterator, TYPE_CHECKING, List, Dict, Any, AsyncGenerator
import json

from core.llm import HelloAgentsLLM
from core.agent import Agent
from core.config import Config
from core.message import Message

class SimpleAgent(Agent):
    """
    简单的对话Agent，支持可选的工具调用

    特性：
    - 纯对话模式
    - function calling 工具调用 （可选）
    - 自动多轮工具调用
    """

