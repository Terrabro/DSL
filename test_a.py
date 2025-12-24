import sys
import os
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from interpreter_core import InterpreterCore
    DSL_DIR = "yaml" 
    NLU_MODEL = "doubao-seed-1-6-251015"
except ImportError as e:
    print(f"错误：无法导入 InterpreterCore 或配置。请确保 interpreter_core.py 文件存在于当前目录。")
    print(f"原始错误: {e}")
    sys.exit(1)


def initialize_interpreter(dsl_dir: str, nlu_model: str) -> InterpreterCore:
    """初始化并启动对话解释器"""
    print("--- 智能多领域机器人解释器 启动 ---")
    try:
        interpreter = InterpreterCore(dsl_dir, nlu_model)
        interpreter._display_prompt(interpreter._get_current_state_def().get("ENTRY_PROMPT"))
        
        welcome_def = interpreter._get_current_state_def()
        if welcome_def.get('ACTION_FULFILLED'):
            transition = welcome_def['ACTION_FULFILLED']['TRANSITIONS'][0] 
            target_state = transition['GOTO']
            interpreter.context.current_state = target_state
            interpreter._display_prompt(interpreter._get_current_state_def().get("ENTRY_PROMPT"))
            
        return interpreter

    except Exception as e:
        print(f"\n[致命错误] 初始化失败: {e}")
        print("请检查：1. ARK_API_KEY 环境变量是否设置；2. YAML 文件是否在指定的 DSL 目录下。")
        sys.exit(1)


def run_test_sequence(interpreter: InterpreterCore, test_cases: List[Dict[str, str]]):
    """运行预设的测试序列，模拟用户输入"""
    
    print("\n" + "="*80)
    print("🤖 启动测试序列 - 验证多域切换和业务流程")
    print("="*80)

    for i, test_case in enumerate(test_cases):
        user_input = test_case['input']
        expected_domain = test_case.get('expected_domain', interpreter.context.current_domain)
        description = test_case.get('description', '无描述')
        
        print(f"\n--- 测试 {i+1}: {description} ---")
        print(f"👤 用户 ({interpreter.context.current_domain} -> {expected_domain}): {user_input}")

        try:
            interpreter.process_turn(user_input)
            
            if interpreter.context.current_domain != expected_domain:
                 print(f"[⚠️ 验证失败]: 领域应为 {expected_domain}，但当前是 {interpreter.context.current_domain}")
            else:
                 print(f"[✅ 验证通过]: 领域匹配成功 ({expected_domain})")
                 
        except Exception as e:
            print(f"\n[致命错误]: 处理输入 '{user_input}' 时发生异常: {e}")
            break

    print("\n" + "="*80)
    print("✅ 测试序列运行结束")
    print("="*80)


if __name__ == "__main__":
    
    TEST_CASES = [
        # 1. 客服流程启动 - 订单查询
        {"input": "我要查订单", "expected_domain": "Customer_Service", "description": "客服：订单查询意图切换"},
        {"input": "O20240904", "expected_domain": "Customer_Service", "description": "客服：订单查询成功（槽位满足与API）"},
        
        # 2. 领域切换：智能家居
        {"input": "我想把卧室的灯打开", "expected_domain": "Smart_Home", "description": "领域切换：客服 -> 智能家居（API 模拟）"},
        
        # 3. 领域切换：金融顾问
        {"input": "查一下苹果股票最近走势", "expected_domain": "Finance_Advisor", "description": "领域切换：智能家居 -> 金融顾问"},
        {"input": "AAPL", "expected_domain": "Finance_Advisor", "description": "金融顾问：槽位填充与 API 模拟"}, 
        
        # 4. 领域切换：客服 - 多槽位业务
        {"input": "我要修改密码", "expected_domain": "Customer_Service", "description": "领域切换：金融顾问 -> 客服，启动多槽位业务"},
        {"input": "账号user1001", "expected_domain": "Customer_Service", "description": "客服：槽位1/3填充"},
        {"input": "旧密码123456，新密码654321", "expected_domain": "Customer_Service", "description": "客服：槽位2/3, 3/3填充，并触发 API 模拟"},
        
        # 5. Fallback 流程测试
        {"input": "一堆乱七八糟的字", "expected_domain": "Customer_Service", "description": "客服：触发 Fallback 机制"},
    ]
    
    # 初始化解释器
    interpreter = initialize_interpreter(DSL_DIR, NLU_MODEL)
    
    # 运行测试序列
    if interpreter.context.session_active:
        run_test_sequence(interpreter, TEST_CASES)