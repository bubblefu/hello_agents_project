from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os

load_dotenv()

model = init_chat_model(
    model=os.getenv("LLM_MODEL_ID"),
    model_provider="openai",
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL").strip(),
    temperature=0,
    # 🔑 extra_body 通过 kwargs 透传
    extra_body={"enable_thinking": False},
)

response = model.invoke("你听过李健的人间共鸣么")
print(response.content)
# for chunk in model.stream(
#     {"messages": [{"role": "user", "content":"你是谁，能解决什么问题？"}]},
  
# ):
#     print(chunk)
#     print("\n")
