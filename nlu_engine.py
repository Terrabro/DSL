import os
import json
from openai import OpenAI
from typing import Dict, List

# --- 配置信息 (用于 NLU 转换的预定义信息) ---
SYSTEM_INSTRUCTIONS = """
你是一个专业的自然语言理解(NLU)引擎。你的唯一职责是深度理解用户的**语义意图**，并以严格的JSON格式输出意图和实体。
请勿输出任何解释、寒暄或额外的文本，只返回一个有效的JSON对象。

任务：根据用户的自然语言表达或选择，将其映射到最符合的预定义意图，并提取所有相关实体。
你的推断应基于语义和上下文，**即使输入不完全符合示例，也应自主推断最可能的意图。**

【预定义信息】
- 意图列表 (Intents)：["ModifyPassword", "DeactivateAccount", "QueryOrder", "QueryProduct", "LodgeComplaint", "Greeting", "Fallback", "Select_1", "Select_2", "Select_3", "Select_4", "Select_5"]
- 实体列表 (Slots)：["order_id", "product_name", "account_id", "old_password", "new_password", "complaint_target", "issue_description"]
- 输出格式：必须是单个JSON对象：{"intent": "<识别到的意图>", "slots": {"<实体名>": "<提取到的值>", ...}}
- **兜底规则：** 只有当用户输入完全无法推断出任何上述意图时，才使用 "Fallback"。

【意图映射示例及推断指引】
重要！！！：
    请自己联系上下文，给出最好的判断。比如在修改密码时上一次输入了账号，第二次输入了密码，自行联系上下文补齐账号。

**1. 账户操作 (修改/注销)**
   - 对应意图：ModifyPassword, DeactivateAccount
   - 语义示例：用户说“账号操作”、“我想换个密码”、“我想把账户关掉”。

**2. 订单查询**
   - 对应意图：QueryOrder
   - 语义示例：用户说“我要查包裹”、“我的快递到哪了”、“订单号是多少”。
   - **特殊规则：** 如果用户提供的订单号是纯数字，请在提取的 `order_id` 前加上大写字母 "O"，以进行标准化（例如：输入“20240911”，提取“O20240911”）。
   
**3. 商品信息查询**
   - 对应意图：QueryProduct
   - 语义示例：用户说“商品问题”、“想查一下手机的价格”、“有没有新的智能手表”。
   
**4. 提交投诉**
   - 对应意图：LodgeComplaint
   - 语义示例：用户说“我有投诉”、“服务态度差”、“对你们很不满意”。

**5. 问候/寒暄**
   - 对应意图：Greeting
   - 语义示例：用户说“你好”、“谢谢”。

**6. 菜单数字选择**
   - 如果用户输入数字 **1**, 意图为 Select_1 (修改密码)
   - 如果用户输入数字 **2**, 意图为 Select_2 (注销账户)
   - 如果用户输入数字 **3**, 意图为 Select_3 (订单查询)
   - 如果用户输入数字 **4**, 意图为 Select_4 (商品查询)
   - 如果用户输入数字 **5**, 意图为 Select_5 (提交投诉)
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