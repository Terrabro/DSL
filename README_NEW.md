# 🤖 DSL 驱动的多域对话系统

这是一个基于领域特定语言（Domain Specific Language, DSL）驱动的智能对话系统项目。它使用 **火山方舟大模型** 作为核心的自然语言理解（NLU）引擎，通过 **DSL (YAML 格式)** 文件灵活定义对话流程、状态转换和业务逻辑，支持多个不同的应用场景（客服、智能家居、财务顾问等）。

项目目标是实现一个**高度可配置、易于扩展、鲁棒性强**的对话系统框架，无需修改核心代码即可快速构建新的对话应用。

## ✨ 核心特性

- **🎯 多域支持**：通过 DSL 文件轻松支持多个独立的对话域（Customer Service、Smart Home、Finance Advisory 等）
- **🧠 模型驱动 NLU**：基于火山方舟大模型的语义理解，支持意图识别和实体抽取
- **📋 完整的 DSL 框架**：声明式定义对话状态、转换、槽位、API 动作等，无代码修改即可改变对话行为
- **💾 真实数据模拟**：CSV 文件模拟数据库，支持订单查询、账户管理、投诉处理等真实业务流程
- **🔄 上下文管理**：完善的对话上下文维护，自动管理对话状态、槽位和 API 结果
- **🛠️ 模块化设计**：解耦的模块结构，便于测试、维护和功能扩展

## 📁 项目结构

```
DSL/
├── 📂 data/                          # 数据模拟层
│   ├── accounts.csv                 # 账户数据
│   ├── orders.csv                   # 订单数据
│   ├── complaints.csv               # 投诉数据
│   └── products.csv                 # 商品数据
│
├── 📂 yaml/                          # DSL 配置层（多域定义）
│   ├── customer_service.yaml        # 客服机器人对话流程
│   ├── smart_home.yaml              # 智能家居控制对话流程
│   └── finance_advisor.yaml         # 财务顾问对话流程
│
├── 📄 核心模块
│   ├── interpreter_core.py          # 对话状态机核心实现
│   ├── nlu_engine.py                # NLU 引擎（LLM 调用与意图识别）
│   ├── dsl_parser.py                # DSL YAML 文件解析器
│   ├── dsl_manager.py               # 多域 DSL 管理器
│   └── data_manager.py              # 数据管理层（CRUD 操作）
│
├── 📄 README.md                      # 项目文档
└── 📄 requirements.txt               # Python 依赖列表
```

## 🏗️ 架构设计

```
用户输入 (自然语言)
    ↓
[NLU Engine] ← 调用火山方舟 API ← 意图识别与实体抽取
    ↓
[Interpreter Core] ← DSL 定义
    ├─ 状态转换
    ├─ 槽位填充
    └─ API 动作执行
    ↓
[Data Manager] ← 访问 CSV 数据库
    ├─ query_order()
    ├─ query_product()
    ├─ submit_complaint()
    └─ change_password()
    ↓
机器人响应 (自然语言)
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install openai pyyaml
```

### 2. 配置 API Key

设置火山方舟大模型的 API 密钥：

**Windows (CMD):**
```bash
set ARK_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:ARK_API_KEY="your_api_key_here"
```

**Linux/macOS (Bash):**
```bash
export ARK_API_KEY="your_api_key_here"
```

### 3. 运行对话系统

```bash
# 运行默认的客服机器人
python interpreter_core.py
```

交互示例：
```
🤖 机器人: 您好！我是智能客服。请问您需要什么帮助？
👤 用户: 我要查订单
🤖 机器人: 好的，请您提供要查询的订单号。
👤 用户: O20240904
🤖 机器人: 您的订单 O20240904 购买了 平板电脑，当前状态是【已发货】，预计到达日期是 2025-12-12。
```

## 📚 模块说明

### `nlu_engine.py` - 自然语言理解引擎
- 调用火山方舟大模型 API
- 解析用户输入，识别意图和实体
- 支持上下文感知的意图识别

**关键函数：**
```python
recognize_intent(model, user_input, current_state, required_slots) -> Dict
```

### `dsl_parser.py` - DSL 解析器
- 加载和解析 YAML 格式的 DSL 定义
- 验证 DSL 结构完整性
- 支持多个 DSL 文件

**关键类：**
```python
class DSL_Parser:
    def load_and_parse(self) -> Dict
```

### `dsl_manager.py` - 多域 DSL 管理器
- 管理多个独立的对话域
- 支持域的动态切换
- 统一的配置加载和管理

**关键类：**
```python
class DSLManager:
    def __init__(self, dsl_dir: str = "yaml")
    def get_config(self, domain: str) -> Dict
```

### `data_manager.py` - 数据管理层
- 从 CSV 文件加载数据
- 实现 CRUD 操作
- 支持数据持久化

**关键方法：**
```python
query_order(order_id)           # 查询订单
query_product(product_name)     # 查询商品
submit_complaint(...)           # 提交投诉
change_password(...)            # 修改密码
```

### `interpreter_core.py` - 对话状态机核心
- 维护对话上下文和状态
- 实现完整的状态转换逻辑
- 协调 NLU、DSL 和数据管理的交互

**关键类：**
```python
class DialogueContext:          # 对话上下文
class InterpreterCore:           # 对话解释器
```

## 📖 DSL 格式说明

### 基本结构

```yaml
FLOW_ID: "Domain_Name"
INITIAL_STATE: "WELCOME"

INTENT_MAP:                    # 意图到状态的映射
  Greeting: MAIN_MENU
  QueryOrder: ORDER_QUERY_START
  ModifyPassword: ACCOUNT_CHANGE_PASSWORD_START

STATES:                        # 状态定义
  WELCOME:
    ENTRY_PROMPT: "欢迎消息"
    REQUIRED_SLOTS: []
    ACTION_FULFILLED:
      TRANSITIONS:
        - CONDITION: ALWAYS
          GOTO: MAIN_MENU
  
  ORDER_QUERY_START:
    REQUIRED_SLOTS: ["order_id"]
    ACTION_MISSING_SLOT:
      PROMPT: "请提供订单号"
    ACTION_FULFILLED:
      EXECUTE: "OrderAPI.query"
      TRANSITIONS:
        - CONDITION: API_SUCCESS
          GOTO: ORDER_QUERY_SUCCESS
        - CONDITION: API_FAILURE
          GOTO: ORDER_QUERY_FAILURE
```

### 关键概念

| 概念 | 说明 |
|------|------|
| **FLOW_ID** | 对话流程的唯一标识符 |
| **INITIAL_STATE** | 对话的初始状态 |
| **INTENT_MAP** | 将用户意图映射到对话状态 |
| **STATES** | 定义所有可能的对话状态 |
| **REQUIRED_SLOTS** | 该状态需要收集的信息槽位 |
| **ENTRY_PROMPT** | 进入该状态时的提示消息 |
| **EXECUTE** | 触发的 API 动作 |
| **TRANSITIONS** | 状态转换规则（基于条件） |

## 🎯 使用场景

### 1. 客户服务（已实现）
- 订单查询
- 账户管理（修改密码、注销账户）
- 投诉处理
- 商品信息查询

### 2. 智能家居（DSL 已定义）
- 灯光控制
- 温度设置
- 设备查询

### 3. 财务顾问（DSL 已定义）
- 账户查询
- 投资建议
- 交易历史查询

## 🔧 扩展指南

### 添加新的对话域

1. **创建 DSL 文件** - 在 `yaml/` 目录中创建新的 YAML 文件
   ```yaml
   # yaml/my_domain.yaml
   FLOW_ID: "My_Domain"
   INITIAL_STATE: "START"
   # ... 定义状态和转换
   ```

2. **更新 DSL Manager** - 在 `dsl_manager.py` 中注册新域
   ```python
   DSL_FILES = {
       "My_Domain": "my_domain.yaml",
       # ...
   }
   ```

3. **扩展 Data Manager** - 如需要，在 `data_manager.py` 中添加新的数据操作
   ```python
   def custom_operation(self, param):
       # 实现业务逻辑
       pass
   ```

4. **在 Interpreter Core 中注册动作** - 在 `_execute_action()` 方法中处理新的 API 调用
   ```python
   elif action_str == "CustomAPI.action":
       result = self.data_manager.custom_operation(slots)
   ```

## 📊 数据格式

### accounts.csv
```csv
account_id,password
user1001,123456
user1002,pa$$word2
```

### orders.csv
```csv
order_id,product_name,status,eta
O20240904,平板电脑,已发货,2025-12-12
O20240905,智能手表,已发货,2025-12-14
```

### products.csv
```csv
product_name,price,stock,description
智能手机X,5999,有货,高性能旗舰手机
蓝牙耳机Pro,999,有货,降噪效果极佳
```

### complaints.csv
```csv
ref_id,account_id,issue_description
C99901,user1001,物流太慢，超过承诺时间。
```

## 🐛 常见问题

### Q: 如何切换对话域？
A: 目前项目支持通过修改 `interpreter_core.py` 中的 `FLOW_FILE_PATH` 来选择不同的 DSL 文件：
```python
FLOW_FILE_PATH = "yaml/customer_service.yaml"  # 改为其他 YAML 文件
```

### Q: 如何自定义 NLU 提示词？
A: 编辑 `nlu_engine.py` 中的 `SYSTEM_INSTRUCTIONS` 常量，修改 NLU 的系统提示词。

### Q: 数据保存是否支持数据库？
A: 当前版本使用 CSV 文件。如需数据库支持，可在 `data_manager.py` 中替换 `_load_csv()` 和 `_save_csv()` 方法。



**最后更新**: 2025年12月10日
