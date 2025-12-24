import sys
import os

# 1. 模拟 NLU 返回值的预设映射表
# 格式: { "用户输入内容": {"domain": "领域名", "intent": "意图名", "slots": {实体数据}} }
MOCK_AI_RESPONSES = {
    "查订单O20240904": {
        "domain": "Customer_Service",
        "intent": "QueryOrder",
        "slots": {"order_id": "O20240904"}
    },
    "我要查订单": {
        "domain": "Customer_Service",
        "intent": "QueryOrder",
        "slots": {}
    },
    "O20240904": {
        "domain": "Customer_Service",
        "intent": "QueryOrder",
        "slots": {"order_id": "O20240904"}
    },
    "打开卧室灯": {
        "domain": "Smart_Home",
        "intent": "ControlDevice",
        "slots": {"device_name": "卧室灯", "action": "打开"}
    },
    "AAPL股票多少钱": {
        "domain": "Finance_Advisor",
        "intent": "QueryMarket",
        "slots": {"stock_symbol": "AAPL"}
    }
}

# 2. 定义桩函数（Stub Functions）来替换真实的 API 调用
def mock_recognize_domain(user_input):
    print(f"[Stub] 正在模拟领域识别: '{user_input}'")
    for key, resp in MOCK_AI_RESPONSES.items():
        if key in user_input or user_input in key:
            return resp["domain"]
    return "Customer_Service"

def mock_recognize_intent(model, user_input, intent_map, current_state, required_slots):
    print(f"[Stub] 正在模拟意图识别: '{user_input}'")
    for key, resp in MOCK_AI_RESPONSES.items():
        if key in user_input or user_input in key:
            return {"intent": resp["intent"], "slots": resp["slots"]}
    return {"intent": "Fallback", "slots": {}}

# 3. 动态替换 nlu_engine 中的函数（Monkey Patching）
import nlu_engine
nlu_engine.recognize_domain = mock_recognize_domain
nlu_engine.recognize_intent = mock_recognize_intent

# 4. 导入并初始化解释器核心
from interpreter_core import InterpreterCore

def run_stub_test():
    print("="*60)
    print("🚀 启动逻辑测试桩 - 模拟 AI 正确输出场景")
    print("="*60)

    # 初始化配置
    DSL_DIR = "yaml"
    NLU_MODEL = "stub-model"
    
    # 初始化解释器（此时内部调用的 NLU 已被替换为 mock 函数）
    interpreter = InterpreterCore(DSL_DIR, NLU_MODEL)
    
    # 模拟启动过程
    interpreter._display_prompt(interpreter._get_current_state_def().get("ENTRY_PROMPT"))
    welcome_def = interpreter._get_current_state_def()
    if welcome_def.get('ACTION_FULFILLED'):
        target_state = welcome_def['ACTION_FULFILLED']['TRANSITIONS'][0]['GOTO']
        interpreter.context.current_state = target_state
        interpreter._display_prompt(interpreter._get_current_state_def().get("ENTRY_PROMPT"))

    # 测试用例序列
    test_inputs = [
        "我要查订单",      # 测试点：意图识别与状态转换
        "O20240904",      # 测试点：槽位填充与 DataManager 查询
        "打开卧室灯",      # 测试点：领域切换 (Customer -> SmartHome)
        "AAPL股票多少钱"   # 测试点：领域切换 (SmartHome -> Finance)
    ]

    for user_input in test_inputs:
        print(f"\n--- 模拟输入: '{user_input}' ---")
        interpreter.process_turn(user_input)
        print(f"当前领域: {interpreter.context.current_domain} | 当前状态: {interpreter.context.current_state}")

    print("\n" + "="*60)
    print("✅ 逻辑测试桩运行完成")
    print("="*60)

if __name__ == "__main__":
    run_stub_test()