import serpapi
import os 
from dotenv import load_dotenv
from typing import Optional, Callable, List, Dict, Any
import json; 
load_dotenv()

def _parse_answer_box(results: Dict[str, Any]) -> Optional[str]:
    box = results.get("answer_box")
    if not isinstance(box, dict):return None
    for key in ("answer", "snippet", "result", "text", "response"):
        value = box.get(key)
        if value:
            if isinstance(value, list):
                return "\n".join(str(v) for v in value if v)
            return str(value).strip()  
    items = box.get("list")
    if isinstance(items, list):
        cleaned = [str(item).strip() for item in items if item]
        if cleaned:
            return "\n".join(cleaned)
    return None

def _parse_answer_box_list(results: Dict[str, Any]) -> Optional[str]:
    boxes = results.get("answer_box_list")
    if not isinstance(boxes, list):
        return None

    texts = []
    for box in boxes:
        if isinstance(box, dict):
            text = box.get("answer") or box.get("snippet") or box.get("text")
            if text:
                texts.append(str(text).strip())
        elif isinstance(box, str):
            texts.append(box)

    return "\n".join(texts) if texts else None

def _parse_sports_results(results: Dict[str, Any]) -> Optional[str]:
    """解析体育赛事结果"""
    sports = results.get("sports_results")
    if not isinstance(sports, dict):
        return None

    lines = []

    # 球队名称
    teams = sports.get("teams")
    if isinstance(teams, list) and len(teams) >= 2:
        names = []
        for t in teams[:2]:
            if isinstance(t, dict) and t.get("name"):
                names.append(t["name"])
        if len(names) == 2:
            lines.append(f"{names[0]} vs {names[1]}")

    # 比分
    score = sports.get("score")
    if score:
        lines.append(f"比分: {score}")

    # 比赛状态（进行中/已结束/未开始）
    state = sports.get("game_state")
    if state:
        lines.append(f"状态: {state}")

    # 比赛摘要（如“快船 112-108 爵士”）
    summary = sports.get("summary")
    if summary:
        lines.append(summary)

    return "\n".join(lines) if lines else None

def _parse_knowledge_graph(results: Dict[str, Any]) -> Optional[str]:
    kg = results.get("knowledge_graph")
    if not isinstance(kg, dict):
        return None

    description = kg.get("description") or kg.get("snippet")
    if not description:
        return None

    title = kg.get("title")
    if title:
        return f"{title}\n{description}"

    return str(description)
def _parse_related_questions(results: Dict[str, Any]) -> Optional[str]:
    questions = results.get("related_questions")
    if not isinstance(questions, list):
        return None

    qa_pairs = []
    for item in questions[:3]:
        if not isinstance(item, dict):
            continue
        q = item.get("question")
        a = item.get("snippet") or item.get("answer")
        if q and a:
            qa_pairs.append(f"Q: {q}\nA: {a}".strip())

    return "\n\n".join(qa_pairs) if qa_pairs else None

def _parse_local_results(results: Dict[str, Any]) -> Optional[str]:
    locals_ = results.get("local_results")
    if not isinstance(locals_, list):
        return None

    lines = []
    for item in locals_[:3]:
        if not isinstance(item, dict):
            continue

        name = item.get("title") or item.get("name")
        if not name:
            continue

        parts = [name]

        address = item.get("address")
        if address:
            parts.append(address)

        rating = item.get("rating")
        if rating:
            parts.append(f"评分 {rating}")

        lines.append(" | ".join(parts))

    return "\n".join(lines) if lines else None
def _parse_organic_results(results: Dict[str, Any]) -> Optional[str]:
    organic = results.get("organic_results")
    if not isinstance(organic, list):
        return None

    snippets = []
    for i, item in enumerate(organic[:3]):
        if not isinstance(item, dict):
            continue

        title = item.get("title", "").strip()
        snippet = item.get("snippet", "").strip()

        # 优先使用完整 snippet，而不是只用高亮词
        if title or snippet:
            full_text = f"{title}\n{snippet}".strip()
            snippets.append(f"[{i+1}] {full_text}")
        else:
            highlighted = item.get("snippet_highlighted_words")
            if highlighted:
                if isinstance(highlighted, list):
                    hl_text = " ".join(str(h) for h in highlighted if h)
                else:
                    hl_text = str(highlighted)
                if hl_text:
                    snippets.append(f"[{i + 1}] {hl_text}")

    return "\n\n".join(snippets) if snippets else None

def _parse_related_searches(results: Dict[str, Any]) -> Optional[str]:
    searches = results.get("related_searches")
    if not isinstance(searches, list):
        return None

    queries = [s.get("query") for s in searches if isinstance(s, dict) and s.get("query")]
    if not queries:
        return None

    return "相关搜索: " + ", ".join(queries[:5])

def smart_parse_results(results: Dict[str, Any], query: str = "") -> Optional[str]:           
    """
    智能解析SerpApi返回的结果，按优先级提取最相关的答案。
    1. 基础校验
    2. 顺序调度 parser
    3. 统一兜底
    """
    if not isinstance(results, dict):
        return None
    
    if "error" in results: 
        return f"搜索出错：{results.get('error', '未知错误')}"
    
    parsers: List[Callable[[Dict[str, Any]], Optional[str]]] = [
        _parse_answer_box,
        _parse_answer_box_list,
        _parse_sports_results,
        _parse_knowledge_graph,
        _parse_related_questions,
        _parse_local_results,
        _parse_organic_results,
        _parse_related_searches,
    ]

    for parser in parsers:
        result = parser(results)
        if result and result.strip():
            return result.strip()
    
    return f"抱歉，没有找到关于'{query}'的相关信息"



def search(query: str) -> str:
    """
    基于SerpApi的实战网页搜索引擎工具，智能解析搜索结果，优先返回 直接答案或者知识图谱信息
    使用SerpApiClient去进行搜索，它是底层class，可以选择搜索引擎；而GoogleSearch只能用Google搜索
    """
    print(f"正在执行【SerpiApi】网页搜索：{query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误：SERPAPI_API_KEY 没有在.env文件中配置"
        
        params = {
            "engine" : "google",
            "q"      :  query,
            "api_key":  api_key,
            "gl"     : "cn",
            "hl"     : "zh-cn",
        }
        client = serpapi.Client(params)
        results = client.get_dict()
        # print(json.dumps(results, indent=2, ensure_ascii=False))
        return smart_parse_results(results, query)
    
    except Exception as e:
        return f"搜索时发生了错误：{e}"


class ToolExecutor:
    """
    工具执行器，负责管理和执行工具
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func:callable):
        """
        向工具箱中注册一个新工具
        """
        if name in self.tools:
            print(f"警告：工具 '{name}'已经存在，将被覆盖。")
        self.tools[name] = {"description": description, "function": func}
        print(f"工具 '{name}' 已注册")

    def getTool(self, name: str) -> callable:
        """ 
        根据名称获取一个工具的执行函数
        """
        return self.tools.get(name, {}).get("function")
    
    def getAvailableTools(self) -> str:
        """ 
        获取所有可用工具的格式化描述字符串
        """
        return "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
    

if __name__ == '__main__':

    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册实战搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search)

    # 3. 打印可用的工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())

    # 4. 智能体的Action调用，这次我们问一个实时问题
    tool_name  = "Search"
    tool_input = input("请输入您要搜索的内容: ")
    print(f"\n\n---执行 Action: Search['{tool_input}'] --- ")
    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察（Observation）---")
        print(observation)
    else:
        print(f"错误：未找到名为：'{tool_name}'的工具。")
