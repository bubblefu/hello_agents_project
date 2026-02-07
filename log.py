import logging
"""
 logger.info 代替流程 print
 logger.debug 打印内部数据
 logger.warning 表示提前终止
 logger.error 记录异常
 level 是“最低显示级别”，不是唯一级别
 DEBUG < INFO < WARNING < ERROR < CRITICAL

    level=INFO
        会显示:INFO / WARNING / ERROR / CRITICAL
        不显示 DEBUG

    level=DEBUG
        全部都会显示
"""

"""
format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
%(asctime)s	    时间
%(levelname)s	日志级别 (INFO / DEBUG / ERROR)
%(name)s	    当前模块名
%(message)s	    你写的内容

举例：2026-02-04 17:12:10 - INFO - reflection_agent - Starting initial attempt...
"""


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
