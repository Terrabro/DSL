# nlu_engine.py
import os
import json
from openai import OpenAI
from typing import Dict, List

# --- 配置信息 (用于 NLU 转换的预定义信息) ---
SYSTEM_INSTRUCTIONS = """
你是一个专业的自然语言理解(NLU)引擎，只负责解析用户输入并以严格的JSON格式输出意图和实体。
请勿输出任何解释、寒暄或额外的文本，只返回一个有效的JSON对象。
任务：将用户输入映射到预定义意图，并提取所有相关的实体。

【预定义信息】
- 意图列表 (Intents)：["ModifyPassword", "DeactivateAccount", "QueryOrder", "QueryProduct", "LodgeComplaint", "Greeting", "Fallback"]
- 实体列表 (Slots)：["order_id", "product_name", "account_id", "old_password", "new_password", "complaint_target", "issue_description"]
- 输出格式：必须是单个JSON对象：{"intent": "<识别到的意图>", "slots": {"<实体名>": "<提取到的值>", ...}}
- 规则：如果无法确定意图，请使用 "Fallback"。如果没有提取到任何实体，"slots" 字段应为空字典 {}。

【意图映射示例】
- 如果用户说“账号操作”、“我想改密码”、“注销”，请使用意图 ModifyPassword 或 DeactivateAccount。
- 如果用户说“我要查包裹”、“订单号是多少”，请使用意图 QueryOrder。
- 如果用户说“商品问题”、“想查手机”，请使用意图 QueryProduct。
- 如果用户说“我有投诉”、“服务态度差”，请使用意图 LodgeComplaint。
- 如果用户说“你好”、“谢谢”，请使用意图 Greeting。
- 如果不符合，请尽量猜测实际意图，并严格遵守上述输出格式。否则使用意图 Fallback。
"""

# 初始化OpenAI客户端，从环境变量中读取您的API Key
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ.get("ARK_API_KEY"),
)

def recognize_intent(
    model: str, 
    user_input: str, 
    current_state: str, 
    required_slots: List[str]
) -> Dict:
    """执行最小化的上下文驱动 NLU 识别功能。"""
    if not os.environ.get("ARK_API_KEY"):
        print("[NLU 错误] 环境变量 ARK_API_KEY 未设置！使用 Fallback。")
        return {"intent": "Fallback", "slots": {}}
        
    context_prompt = f"""
    【当前对话上下文】
    - 当前状态 (Current State)：{current_state}
    - 当前所需实体 (Required Slots)：{required_slots} 

    【用户输入】
    用户输入: {user_input}
    """
    
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": context_prompt}
    ]
    
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0 # 降低温度
        )
        
        json_text = resp.choices[0].message.content.strip()
        
        # 清理代码块标记
        if json_text.startswith("```json"):
            json_text = json_text.strip("```json").strip("```").strip()
            
        return json.loads(json_text)
        
    except Exception as e:
        print(f"[NLU 错误] API 调用或 JSON 解析失败: {e}")
        return {"intent": "Fallback", "slots": {}}