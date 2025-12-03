# interpreter_core.py V2.0

import json
import time
import os
from typing import Dict, List, Any

# --- 导入依赖 ---
from nlu_engine import recognize_intent
from dsl_parser import DSL_Parser
from data_manager import DataManager # V2.0 新增: 导入数据管理器

# --- 全局配置 ---
FLOW_FILE_PATH = "customer_service_flow.yaml"
NLU_MODEL = "doubao-seed-1-6-lite-251015" 

# --- 解释器核心数据结构 ---
class DialogueContext:
    def __init__(self, initial_state: str):
        self.current_state = initial_state
        self.slots_filled = {}
        self.api_result = {}
        self.session_active = True
        
class InterpreterCore:
    def __init__(self, flow_file: str, nlu_model: str):
        self.nlu_model = nlu_model
        
        # 1. 加载 DSL 规则
        parser = DSL_Parser(flow_file)
        self.flow_model = parser.load_and_parse()
        
        # V2.0 新增: 初始化数据管理器
        self.data_manager = DataManager()
        
        # 2. 初始化上下文
        initial_state = self.flow_model.get("INITIAL_STATE")
        self.context = DialogueContext(initial_state)

    def _get_current_state_def(self) -> dict:
        return self.flow_model['STATES'].get(self.context.current_state, {})

    def _execute_action(self, action_str: str, slots: dict) -> dict:
        """ V2.1: 调用 DataManager 执行真实的查询/修改操作。 """
        print(f"\n[执行动作]: 调用 DataManager -> {action_str}")
        
        result_payload: Dict[str, Any] = {}
        
        if action_str == "OrderAPI.query":
            order_info = self.data_manager.query_order(slots.get('order_id'))
            if order_info:
                result_payload = {"status": "success", "api_result": order_info}
            else:
                result_payload = {"status": "failure", "api_result": {"message": "订单不存在"}}

        elif action_str == "ProductAPI.query": # V2.1 新增：商品查询
            product_info = self.data_manager.query_product(slots.get('product_name', ''))
            if product_info:
                result_payload = {"status": "success", "api_result": product_info}
            else:
                result_payload = {"status": "failure", "api_result": {"message": "商品不存在"}}
                
        elif action_str == "AccountAPI.changePassword":
            success = self.data_manager.change_password(
                slots.get('account_id'), slots.get('old_password'), slots.get('new_password')
            )
            if success:
                result_payload = {"status": "success"}
            else:
                result_payload = {"status": "failure", "api_result": {"message": "账户或密码错误"}}

        elif action_str == "AccountAPI.deactivate":
            success = self.data_manager.deactivate_account(slots.get('account_id'))
            if success:
                result_payload = {"status": "success"}
            else:
                result_payload = {"status": "failure", "api_result": {"message": "账户不存在"}}

        elif action_str == "ComplaintAPI.submit":
            ref_data = self.data_manager.submit_complaint(
                slots.get('account_id', '未提供'),
                slots.get('issue_description')
            )
            result_payload = {"status": "success", "api_result": ref_data}
            
        else:
            result_payload = {"status": "success", "api_result": {"message": "操作成功"}}
            
        return result_payload

    def _all_slots_filled(self, state_def: dict) -> bool:
        required = set(state_def.get("REQUIRED_SLOTS", []))
        # 检查是否所有必需的槽位都有值，并且值不是空字符串
        filled = {k for k, v in self.context.slots_filled.items() if v is not None and str(v).strip() != ''}
        return required.issubset(filled)

    # (其余的辅助函数 _get_current_state_def, _resolve_prompt, _display_prompt, 
    #  以及核心逻辑 process_turn, _check_slots_and_act 保持不变或进行微调)
    # --------------------------------------------------------------------------------

    def _resolve_prompt(self, prompt_template: str) -> str:
        """替换 PROMPT 模板中的变量。"""
        final_prompt = prompt_template
        for key, value in self.context.slots_filled.items():
            final_prompt = final_prompt.replace(f"${{{key}}}", str(value))
        if 'api_result' in self.context.api_result and self.context.api_result['status'] == 'success':
             for key, value in self.context.api_result['api_result'].items():
                final_prompt = final_prompt.replace(f"${{api_result.{key}}}", str(value))
        return final_prompt

    def process_turn(self, user_input: str):
        if not self.context.session_active: return

        current_def = self._get_current_state_def()
        required_slots = current_def.get("REQUIRED_SLOTS", [])
        
        # 1. NLU 识别
        nlu_result = recognize_intent(
            model=self.nlu_model,
            user_input=user_input, 
            current_state=self.context.current_state, 
            required_slots=required_slots
        )
        
        print(f"[NLU 结果]: {nlu_result['intent']} | Slots: {nlu_result['slots']}")
        
        # 2. 更新槽位
        self.context.slots_filled.update(nlu_result['slots'])
        
        # 3. 意图驱动的状态转换
        intent = nlu_result['intent']
        if intent in self.flow_model['INTENT_MAP']:
            new_state = self.flow_model['INTENT_MAP'][intent]
            # 特殊处理：如果NLU识别到意图，但当前在MAIN_MENU，则允许跳转
            if new_state != self.context.current_state or self.context.current_state == "MAIN_MENU":
                print(f"[流程转换]: 意图切换 -> 从 {self.context.current_state} 切换到 {new_state}")
                
                # 清理槽位，准备进入新流程
                self.context.slots_filled = {}
                self.context.api_result = {}
                
                self.context.current_state = new_state
                current_def = self._get_current_state_def()
                
                # 切换后，立即检查是否需要执行动作或提问
                if current_def.get("REQUIRED_SLOTS") or current_def.get("ACTION_FULFILLED"):
                    # 如果新状态是需要收集参数的状态，则跳过 ENTRY_PROMPT，直接检查槽位
                    return self._check_slots_and_act(current_def)
                else:
                    self._display_prompt(current_def.get("ENTRY_PROMPT"))
                    return

        # 4. 槽位填充和动作执行 (仅在当前状态下进行)
        self._check_slots_and_act(current_def)


    def _check_slots_and_act(self, state_def: dict):
        if self._all_slots_filled(state_def):
            # 槽位已满足，执行主动作
            action_def = state_def.get("ACTION_FULFILLED", {})
            action_type = action_def.get("EXECUTE")
            
            if action_type:
                api_response = self._execute_action(action_type, self.context.slots_filled)
                self.context.api_result = api_response
                
                # 清理槽位：动作执行完成后，当前流程的槽位清空
                self.context.slots_filled = {}
                
                # 检查转换条件
                for transition in action_def.get("TRANSITIONS", []):
                    condition = transition.get("CONDITION")
                    target_state = transition.get("GOTO")
                    
                    if (condition == "API_SUCCESS" and api_response.get("status") == "success") or \
                       (condition == "API_FAILURE" and api_response.get("status") == "failure"):
                        self.context.current_state = target_state
                        self._display_prompt(self._get_current_state_def().get("ENTRY_PROMPT"))
                        return
            
            # 如果没有 EXECUTE，输出 ENTRY_PROMPT
            self._display_prompt(state_def.get("ENTRY_PROMPT"))

        else:
            # 槽位未满足，执行询问动作
            missing_prompt = state_def.get("ACTION_MISSING_SLOT", {}).get("PROMPT")
            self._display_prompt(missing_prompt)
            
    # --------------------------------------------------------------------------------
    # (其余的 _display_prompt, run_cli_bot 和 __main__ 块保持不变)
    # --------------------------------------------------------------------------------

    def _display_prompt(self, prompt: str):
        if prompt == "END_SESSION":
            self.context.session_active = False
            return
        final_prompt = self._resolve_prompt(prompt)
        print(f"\n🤖 机器人: {final_prompt}")

# --- 主运行循环 (模拟命令行界面) ---
def run_cli_bot(interpreter: InterpreterCore):
    interpreter._display_prompt(interpreter._get_current_state_def().get("ENTRY_PROMPT"))
    
    # 初始状态 WELCOME 执行后，自动跳转到 MAIN_MENU
    if interpreter.context.current_state == "WELCOME":
        interpreter._check_slots_and_act(interpreter._get_current_state_def())

    while interpreter.context.session_active:
        user_input = input("\n👤 用户: ")
        if user_input.lower() in ["退出", "exit", "bye"]:
            interpreter.context.session_active = False
            print("会话结束。")
            break
        try:
            interpreter.process_turn(user_input)
        except Exception as e:
            print(f"\n[解释器运行错误]: {e}")
            if 'Fallback' in interpreter.flow_model['INTENT_MAP']:
                 interpreter.context.current_state = interpreter.flow_model['INTENT_MAP']['Fallback']
                 interpreter._display_prompt(interpreter._get_current_state_def().get("ENTRY_PROMPT"))

if __name__ == "__main__":
    print("--- 智能客服机器人解释器 V2.0 启动 ---")
    try:
        # V2.0 需要确保 data_manager.py 及其依赖的 CSV 文件都存在
        interpreter = InterpreterCore(FLOW_FILE_PATH, NLU_MODEL)
        run_cli_bot(interpreter)
    except Exception as e:
        print(f"\n[致命错误] 初始化失败: {e}")
        print("请检查：1. ARK_API_KEY 环境变量是否设置；2. CSV 文件、YAML 文件和所有 Python 文件是否存在。")