# dsl_parser.py
import yaml
import os

class DSL_Parser:
    """
    负责读取 DSL (YAML) 文件并将其转换为内存中的流程模型。
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.flow_model = None

    def load_and_parse(self):
        """加载 YAML 文件并进行基本的结构验证。"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"错误：DSL 文件未找到在路径: {self.file_path}")

        print(f"--- 正在加载 DSL 文件: {self.file_path} ---")
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.flow_model = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"DSL 解析错误 (YAML 格式不正确): {e}")
            
        # 简化验证
        required_keys = ["FLOW_ID", "INITIAL_STATE", "INTENT_MAP", "STATES"]
        if not all(key in self.flow_model for key in required_keys):
            missing = [key for key in required_keys if key not in self.flow_model]
            raise ValueError(f"DSL 结构验证失败：缺少必需的顶级字段: {missing}")

        print("DSL 文件加载成功。")
        return self.flow_model