## 1. 结果展示
1. 环境搭建完成。目前使用的是WSL2 + vs code 的Linux环境，不是Windows环境。
2. TAVILY API测试完成
 ![alt text](image.png)  
3. FirstAgentTest.py成功运行
   ![alt text](image-1.png)
## 2. 代码分析
- code flow：


程序启动 -> 加载环境变量 (API Key 等) -> 注册工具函数 (get_weather, get_attraction) -> 初始化 LLM 客户端 -> 接收用户初始请求 -> 进入 ReAct 主循环 (设定最大 5 次) -> 拼接对话历史与系统提示词 -> 调用 LLM 生成文本 -> 正则截断多余内容 -> 提取 Action 字段 -> 判断行动类型 -> 若是 Finish -> 提取最终答案 -> 打印结果 -> 结束程序 | 若是工具调用 -> 解析工具名与参数 -> 执行本地 Python 函数 -> 捕获异常并返回 Observation -> 将观察结果追加到对话历史 -> 回到循环开头进行下一轮推理


- 设计思路分析：


核心范式 -> ReAct (Reason + Act) -> 让 LLM 自主规划步骤而非硬编码流程 -> 架构解耦 -> 工具层独立封装 (易扩展新增能力) -> 客户端适配层 (屏蔽不同模型 API 差异) -> 状态管理 -> 利用 Prompt History 实现短期记忆 -> 外部计数器控制循环 (防止死循环与资源耗尽) -> 容错机制 -> 工具内部 Try/Catch (单点失败不崩全局) -> 正则解析 (将非结构化文本转为结构化指令) -> 交互协议 -> 严格定义 Thought/Action 格式 -> 确保机器可解析 -> 实现闭环控制
## 3. tips ＆ debug
1. 直接运行代码，出现了一个问题
   ```python
   Traceback (most recent call last):
    File "/home/bubble/hello_agents_project/FirstAgent317.py", line 192, in <module>
    final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    AttributeError: 'NoneType' object has no attribute 'group'
   ```
   **分析：** 
      ```
   final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
    ```
   查看输出可知，目前正则表达式，没办法匹配Finsh[  中间有换行符   ]的格式。因为Finish\[(.*)\] 中的 *.** 默认不匹配换行符，而LLM可能会输出一个带换行符的[]。 会在第一个换行处停止，无法匹配到最后的 ]，导致整个模式匹配失败，返回 None。对 None 调用 .group(1) 自然抛出 AttributeError。
   
   **解决方案：** 需要让点号 . 能够匹配换行符，使用 re.DOTALL（或 re.S）标志即可：

    

2. 关于API_KEY的环境载入。
   1. 修改成.env 的方式，能统一所有key的信息在一个管理文件中，后续修改和添加都很方便。
   2. load_env()函数可以实现查找母目录和其他子目录中.env文件的功能，使得一个project只有一个.env文件即可。
      1. 如果load_env()没有找到env_path，就会调用find_env()去查找。