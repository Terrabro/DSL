import yaml
import os
from typing import Dict, Any

# 定义领域到文件的映射
DSL_FILES: Dict[str, str] = {
    "Customer_Service": "customer_service.yaml",
    "Smart_Home": "smart_home.yaml",
    "Finance_Advisor": "finance_advisor.yaml",
}

class DSLManager:
    """管理所有领域DSL配置和当前对话状态"""
    
    def __init__(self, dsl_dir: str = "yaml"):
        self.dsl_dir = dsl_dir
        self.configs: Dict[str, Dict[str, Any]] = {}
        self._load_all_dsls()
        
    def _load_all_dsls(self):
        """加载所有 DSL 配置文件"""
        print("--- 正在加载 DSL 配置 ---")
        for domain, filename in DSL_FILES.items():
            filepath = os.path.join(self.dsl_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.configs[domain] = yaml.safe_load(f)
                print(f"成功加载 DSL: {domain} ({filename})")
            except FileNotFoundError:
                print(f"警告: 找不到 DSL 文件: {filepath}")
            except yaml.YAMLError as e:
                print(f"错误: 解析 DSL 文件失败 ({filename}): {e}")
        print("--------------------------")

    def get_config(self, domain: str) -> Dict[str, Any]:
        """根据领域名称获取 DSL 配置"""
        return self.configs.get(domain, {})

    def get_initial_state(self, domain: str) -> str:
        """获取特定领域的初始状态"""
        config = self.get_config(domain)
        return config.get("INITIAL_STATE", "WELCOME")

    def get_intent_map(self, domain: str) -> Dict[str, str]:
        """获取特定领域的意图映射"""
        config = self.get_config(domain)
        return config.get("INTENT_MAP", {})