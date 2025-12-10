import json
import time
import os
import csv
from typing import Dict, List, Any, Optional

# --- 导入依赖 ---
from nlu_engine import recognize_intent, recognize_domain
from dsl_manager import DSLManager
# from dsl_parser import DSL_Parser # 不再使用

# --- 核心辅助类 (DataManager 和 DSL_Parser 保持不变) ---

ACCOUNTS_FILE = "./data/accounts.csv"
ORDERS_FILE = "./data/orders.csv"
COMPLAINTS_FILE = "./data/complaints.csv"
PRODUCTS_FILE = "./data/products.csv"

class DataManager:
    def __init__(self):
        self._data: Dict[str, List[Dict[str, str]]] = {
            'accounts': self._load_csv(ACCOUNTS_FILE),
            'orders': self._load_csv(ORDERS_FILE),
            'complaints': self._load_csv(COMPLAINTS_FILE),
            'products': self._load_csv(PRODUCTS_FILE)
        }
        print("--- DataManager: CSV 数据加载完成 ---")

    def _load_csv(self, file_path: str) -> List[Dict[str, str]]:
        if not os.path.exists(file_path):
            print(f"警告: 文件 {file_path} 不存在，初始化为空列表。")
            return []
        
        data = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    data.append(dict(row))
        except Exception as e:
            print(f"错误: 加载 {file_path} 失败: {e}")
            return []
        return data

    def _save_csv(self, file_path: str, data: List[Dict[str, str]]):
        if not data:
            return
            
        fieldnames = list(data[0].keys())
        try:
            with open(file_path, mode='w', encoding='utf-8', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"[数据操作]: 成功保存数据到 {file_path}")
        except Exception as e:
            print(f"错误: 写入 {file_path} 失败: {e}")

    def query_order(self, order_id: str) -> Optional[Dict[str, str]]:
        for order in self._data['orders']:
            if order.get('order_id', '').strip() == order_id.strip():
                return {
                    'status': order['status'],
                    'eta': order['eta'],
                    'product_name': order['product_name']
                }
        return None

    def query_product(self, product_name: str) -> Optional[Dict[str, str]]:
        search_name_lower = product_name.lower()
        
        for product in self._data['products']:
            if search_name_lower in product.get('product_name', '').lower():
                return product
        return None

    def submit_complaint(self, account_id: str, issue_description: str) -> Dict[str, Any]:
        new_ref_id = f"C{int(time.time())}"
        new_complaint = {
            'ref_id': new_ref_id,
            'account_id': account_id if account_id else "Guest",
            'issue_description': issue_description
        }
        self._data['complaints'].append(new_complaint)
        self._save_csv(COMPLAINTS_FILE, self._data['complaints'])
        return {'ref_id': new_ref_id}

    def change_password(self, account_id: str, old_password: str, new_password: str) -> bool:
        found = False
        success = False
        for account in self._data['accounts']:
            if account.get('account_id') == account_id:
                found = True
                if account.get('password') == old_password:
                    account['password'] = new_password
                    success = True
                    break
                else:
                    success = False
                    break
        if success:
            self._save_csv(ACCOUNTS_FILE, self._data['accounts'])
            return True
        return False
        
    def deactivate_account(self, account_id: str, old_password: str) -> bool:
        found_and_matched = False
        
        for account in self._data['accounts']:
            if account.get('account_id') == account_id:
                if account.get('password') == old_password:
                    found_and_matched = True
                break

        if found_and_matched:
            self._data['accounts'] = [
                account for account in self._data['accounts'] 
                if account.get('account_id') != account_id
            ]
            self._save_csv(ACCOUNTS_FILE, self._data['accounts'])
            return True
        
        return False
        
class DSL_Parser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.flow_model = None

    def load_and_parse(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"错误：DSL 文件未找到在路径: {self.file_path}")

        print(f"--- 正在加载 DSL 文件: {self.file_path} ---")
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.flow_model = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"DSL 解析错误 (YAML 格式不正确): {e}")
            
        required_keys = ["FLOW_ID", "INITIAL_STATE", "INTENT_MAP", "STATES"]
        if not all(key in self.flow_model for key in required_keys):
            missing = [key for key in required_keys if key not in self.flow_model]
            raise ValueError(f"DSL 结构验证失败：缺少必需的顶级字段: {missing}")

        print("DSL 文件加载成功。")
        return self.flow_model

# --- 主控逻辑 ---

# --- 全局配置 ---
DSL_DIR = "yaml" 
NLU_MODEL = "doubao-seed-1-6-lite-251015" 

class DialogueContext:
    def __init__(self, initial_state: str):
        self.current_state = initial_state
        self.slots_filled = {}
        self.api_result = {}
        self.session_active = True
        self.current_domain = "Customer_Service"

class InterpreterCore:
    def __init__(self, dsl_dir: str, nlu_model: str):
        self.nlu_model = nlu_model
        
        self.dsl_manager = DSLManager(dsl_dir)
        self.data_manager = DataManager()
        
        initial_domain = "Customer_Service"
        initial_state = self.dsl_manager.get_initial_state(initial_domain)
        self.context = DialogueContext(initial_state)
        self.context.current_domain = initial_domain

    def _get_current_flow_model(self) -> dict:
        return self.dsl_manager.get_config(self.context.current_domain)

    def _get_current_state_def(self) -> dict:
        flow_model = self._get_current_flow_model()
        return flow_model['STATES'].get(self.context.current_state, {})

    def _execute_action(self, action_str: str, slots: dict) -> dict:
        print(f"\n[执行动作]: 调用 DataManager -> {action_str}")
        
        result_payload: Dict[str, Any] = {}
        
        if action_str == "OrderAPI.query":
            order_info = self.data_manager.query_order(slots.get('order_id'))
            if order_info:
                result_payload = {"status": "success", "api_result": order_info}
            else:
                result_payload = {"status": "failure", "api_result": {"message": "订单不存在"}}

        elif action_str == "ProductAPI.query":
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
            success = self.data_manager.deactivate_account(
                slots.get('account_id'), 
                slots.get('old_password')
            )
            if success:
                result_payload = {"status": "success"}
            else:
                result_payload = {"status": "failure", "api_result": {"message": "账户不存在或密码错误"}}

        elif action_str == "ComplaintAPI.submit":
            ref_data = self.data_manager.submit_complaint(
                slots.get('account_id', '未提供'),
                slots.get('issue_description')
            )
            result_payload = {"status": "success", "api_result": ref_data}
            
        # --- 扩展：智能家居/金融的 API 动作 (占位符) ---
        elif action_str.startswith("DeviceAPI.") or action_str.startswith("SceneAPI."):
            result_payload = {"status": "success", "api_result": {"status": "已完成", "detail": "设备控制指令已发送。"}}
        elif action_str.startswith("MarketAPI.") or action_str.startswith("AccountAPI."):
            result_payload = {"status": "success", "api_result": {"price": "150.00", "change_percent": "+1.5%", "order_id": "T7788"}}
        
        else:
            result_payload = {"status": "success", "api_result": {"message": "操作成功"}}
            
        return result_payload

    def _all_slots_filled(self, state_def: dict) -> bool:
        required = set(state_def.get("REQUIRED_SLOTS", []))
        filled = {k for k, v in self.context.slots_filled.items() if v is not None and str(v).strip() != ''}
        return required.issubset(filled)

    def _resolve_prompt(self, prompt_template: str) -> str:
        final_prompt = prompt_template
        
        for key, value in self.context.slots_filled.items():
            final_prompt = final_prompt.replace(f"${{{key}}}", str(value))
            
        if 'api_result' in self.context.api_result and self.context.api_result['status'] == 'success':
            for key, value in self.context.api_result['api_result'].items():
                final_prompt = final_prompt.replace(f"${{api_result.{key}}}", str(value))
                
        return final_prompt

    def _display_prompt(self, prompt: str):
        if prompt == "END_SESSION":
            self.context.session_active = False
            return
        final_prompt = self._resolve_prompt(prompt)
        print(f"\n🤖 机器人: {final_prompt}")

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
                        
                        target_def = self._get_current_flow_model()['STATES'].get(target_state, {})
                        self.context.current_state = target_state
                        self._display_prompt(target_def.get("ENTRY_PROMPT"))
                        
                        self.context.slots_filled = {}
                        self.context.api_result = {}

                        return
            
            self._display_prompt(state_def.get("ENTRY_PROMPT"))

        else:
            missing_prompt = state_def.get("ACTION_MISSING_SLOT", {}).get("PROMPT")
            self._display_prompt(missing_prompt)
            
    def process_turn(self, user_input: str):
        if not self.context.session_active: return

        current_def = self._get_current_state_def()
        required_slots = current_def.get("REQUIRED_SLOTS", [])
        
        flow_model = self._get_current_flow_model()
        current_intent_map = self.dsl_manager.get_intent_map(self.context.current_domain)
        
        # --- 1. 领域切换逻辑 ---
        if self.context.current_state in ["WELCOME", "MAIN_MENU"]:
            predicted_domain = recognize_domain(user_input)
            
            if predicted_domain != self.context.current_domain:
                print(f"[系统] 领域切换：从 {self.context.current_domain} -> {predicted_domain}")
                
                self.context.current_domain = predicted_domain
                self.context.current_state = self.dsl_manager.get_initial_state(predicted_domain)
                self.context.slots_filled = {}
                self.context.api_result = {}
                
                flow_model = self._get_current_flow_model()
                current_def = self._get_current_state_def()
                current_intent_map = self.dsl_manager.get_intent_map(predicted_domain)
                required_slots = current_def.get("REQUIRED_SLOTS", [])

        # --- 2. NLU 识别 ---
        nlu_result = recognize_intent(
            model=self.nlu_model,
            user_input=user_input, 
            intent_map=current_intent_map,
            current_state=self.context.current_state, 
            required_slots=required_slots
        )
        
        print(f"[NLU 结果]: {nlu_result['intent']} | Slots: {nlu_result['slots']}")
        
        # 3. 更新槽位
        self.context.slots_filled.update(nlu_result['slots']) 

        # 4. 意图驱动的状态转换
        intent = nlu_result['intent']
        if intent in flow_model['INTENT_MAP']:
            new_state = flow_model['INTENT_MAP'][intent]
            
            if new_state != self.context.current_state or self.context.current_state == "MAIN_MENU": 
                print(f"[流程转换]: 意图切换 -> 从 {self.context.current_state} 切换到 {new_state}")

                target_def = flow_model['STATES'].get(new_state, {})
                required_slots_for_new_state = target_def.get("REQUIRED_SLOTS", [])
                
                slots_are_sufficient = all(slot in self.context.slots_filled for slot in required_slots_for_new_state)

                if not slots_are_sufficient:
                    print("[槽位清理]: 意图切换但槽位不足，清空旧槽位。")
                    self.context.slots_filled = {}
                else:
                    print("[槽位保留]: 意图切换但槽位已满足，保留槽位直接执行。")
                    pass 

                self.context.api_result = {} 
                self.context.current_state = new_state
                current_def = target_def 
                
                if current_def.get("REQUIRED_SLOTS") or current_def.get("ACTION_FULFILLED"):
                    return self._check_slots_and_act(current_def) 
                else:
                    self._display_prompt(current_def.get("ENTRY_PROMPT"))
                    return

        # 5. 槽位填充和动作执行 (仅在当前状态下进行)
        self._check_slots_and_act(current_def)

    def run_cli(self):
        """运行命令行界面的对话循环"""
        
        # 1. 打印 WELCOME 提示
        self._display_prompt(self._get_current_state_def().get("ENTRY_PROMPT"))
        
        # 2. 强制执行 WELCOME -> MAIN_MENU 的跳转
        welcome_def = self._get_current_state_def()
        if welcome_def.get('ACTION_FULFILLED'):
            action_def = welcome_def['ACTION_FULFILLED']
            transition = action_def['TRANSITIONS'][0] 
            
            target_state = transition['GOTO']
            self.context.current_state = target_state
            target_def = self._get_current_state_def()
            
            self._display_prompt(target_def.get("ENTRY_PROMPT"))
            
        while self.context.session_active:
            user_input = input(f"\n👤 用户 ({self.context.current_domain}): ")
            if user_input.lower() in ["退出", "exit", "bye"]:
                self.context.session_active = False
                print("会话结束。")
                break
            try:
                self.process_turn(user_input)
            except Exception as e:
                print(f"\n[解释器运行错误]: {e}")
                flow_model = self._get_current_flow_model()
                if 'Fallback' in flow_model.get('INTENT_MAP', {}):
                    self.context.current_state = flow_model['INTENT_MAP']['Fallback']
                    self._display_prompt(self._get_current_state_def().get("ENTRY_PROMPT"))


if __name__ == "__main__":
    print("--- 智能多领域机器人解释器 启动 ---")
    try:
        # 确保 DSL_DIR 指向正确的 yaml 文件目录 (例如: 'C:\\Users\\syk12\\Desktop\\DSL\\yaml')
        interpreter = InterpreterCore(DSL_DIR, NLU_MODEL) 
        interpreter.run_cli()
    except Exception as e:
        print(f"\n[致命错误] 初始化失败: {e}")
        print("请检查：1. ARK_API_KEY 环境变量是否设置；2. YAML 文件是否在指定的 DSL 目录下。")