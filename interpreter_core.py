# interpreter_core.py
import json
import time
import os
from typing import Dict, List

# --- 导入依赖 ---
# 请确保 nlu_engine.py 和 dsl_parser.py 位于同级目录
from nlu_engine import recognize_intent
from dsl_parser import DSL_Parser

# --- 全局配置 ---
FLOW_FILE_PATH = "customer_service_flow.yaml"
NLU_MODEL = "doubao-seed-1-6-lite-251015" 

# --- 解释器核心逻辑 ---
class DialogueContext:
    """维护当前对话的上下文和状态。"""
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
        
        # 2. 初始化上下文
        initial_state = self.flow_model.get("INITIAL_STATE")
        self.context = DialogueContext(initial_state)

    def _get_current_state_def(self) -> dict:
        return self.flow_model['STATES'].get(self.context.current_state, {})

    def _execute_action(self, action_str: str, slots: dict) -> dict:
        """模拟外部 API 调用。"""
        print(f"\n[执行动作]: 调用外部服务 -> {action_str}")
        if "API_FAILURE" in action_str:
            return {"status": "failure", "message": "模拟 API 失败"}
        if "OrderAPI.query" in action_str:
            return {"status": "success", "api_result": {"status": "已发货", "eta": "2025-12-05"}}
        if "ComplaintAPI.submit" in action_str:
            return {"status": "success", "api_result": {"ref_id": "C"+str(int(time.time()))}}
        return {"status": "success", "api_result": {"message": "操作成功"}}

    def _all_slots_filled(self, state_def: dict) -> bool:
        required = set(state_def.get("REQUIRED_SLOTS", []))
        filled = set(self.context.slots_filled.keys())
        return required.issubset(filled)

    def _resolve_prompt(self, prompt_template: str) -> str:
        """替换 PROMPT 模板中的变量。"""
        final_prompt = prompt_template
        for key, value in self.context.slots_filled.items():
            final_prompt = final_prompt.replace(f"${{{key}}}", str(value))
        if 'api_result' in self.context.api_result:
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
            if new_state != self.context.current_state:
                print(f"[流程转换]: 意图切换 -> 从 {self.context.current_state} 切换到 {new_state}")
                self.context.current_state = new_state
                current_def = self._get_current_state_def()
                self._display_prompt(current_def.get("ENTRY_PROMPT"))
                if current_def.get("REQUIRED_SLOTS") or current_def.get("ACTION_FULFILLED"):
                    return self._check_slots_and_act(current_def)
                return

        # 4. 槽位填充和动作执行
        self._check_slots_and_act(current_def)

    def _check_slots_and_act(self, state_def: dict):
        if self._all_slots_filled(state_def):
            action_def = state_def.get("ACTION_FULFILLED", {})
            action_type = action_def.get("EXECUTE")
            
            if action_type:
                api_response = self._execute_action(action_type, self.context.slots_filled)
                self.context.api_result = api_response
                
                for transition in action_def.get("TRANSITIONS", []):
                    condition = transition.get("CONDITION")
                    target_state = transition.get("GOTO")
                    if (condition == "API_SUCCESS" and api_response.get("status") == "success") or \
                       (condition == "API_FAILURE" and api_response.get("status") == "failure"):
                        self.context.current_state = target_state
                        self._display_prompt(self._get_current_state_def().get("ENTRY_PROMPT"))
                        return
            
            self._display_prompt(state_def.get("ENTRY_PROMPT"))

        else:
            missing_prompt = state_def.get("ACTION_MISSING_SLOT", {}).get("PROMPT")
            self._display_prompt(missing_prompt)

    def _display_prompt(self, prompt: str):
        if prompt == "END_SESSION":
            self.context.session_active = False
            return
        final_prompt = self._resolve_prompt(prompt)
        print(f"\n机器人: {final_prompt}")

# --- 主运行循环 ---
def run_cli_bot(interpreter: InterpreterCore):
    interpreter._display_prompt(interpreter._get_current_state_def().get("ENTRY_PROMPT"))
    while interpreter.context.session_active:
        user_input = input("\n用户: ")
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
    print("--- 智能客服机器人解释器启动 ---")
    try:
        interpreter = InterpreterCore(FLOW_FILE_PATH, NLU_MODEL)
        run_cli_bot(interpreter)
    except Exception as e:
        print(f"\n[致命错误] 初始化失败: {e}")
        print("请检查：1. ARK_API_KEY 环境变量是否设置；2. YAML 文件和 Python 文件是否存在。")