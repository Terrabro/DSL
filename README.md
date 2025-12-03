# 🤖 DSL 驱动的智能客服机器人 (Dialogue System using DSL)

这是一个基于领域特定语言（Domain Specific Language, DSL）驱动的对话系统项目。它使用 **火山方舟大模型** 作为核心的自然语言理解（NLU）引擎，并通过 **DSL (YAML 格式)** 文件来定义对话流程、状态转换和业务逻辑。

项目目标是实现一个高可配置、高鲁棒性的智能客服系统原型，能够处理订单查询、账户管理和投诉等业务。

apikey: 17d85748-d826-4455-b95f-8172f284208f

## ✨ 主要特性

* **模型驱动 NLU：** 使用火山方舟大模型（通过 OpenAI SDK 兼容）进行意图识别和实体抽取。
* **DSL 驱动流程：** 对话逻辑完全由 `customer_service_flow.yaml` 文件控制，易于修改和扩展。
* **真实数据模拟：** 使用 CSV 文件模拟后台数据库，通过 `data_manager.py` 实现对账户、订单、投诉和商品的真实查询和模拟操作。
* **上下文管理：** `InterpreterCore` 负责维护对话状态、已收集的槽位（Slots）和 API 结果。

## 📁 文件结构

```
  DSL/  ├── accounts.csv # 账户数据 (模拟数据库) 
        ├── orders.csv # 订单数据 (模拟数据库) 
        ├── complaints.csv # 投诉数据 (模拟数据库) 
        ├── products.csv # 商品数据 (模拟数据库) 
        ├── customer_service_flow.yaml # 对话流程定义文件 (DSL) 
        ├── interpreter_core.py # 主程序和核心解释器 (State Machine) 
        ├── nlu_engine.py # NLU 封装 (API 调用和提示词) 
        ├── dsl_parser.py # DSL 文件加载和解析工具 
        ├── data_manager.py # 数据管理和业务逻辑 (CRUD 操作) 
        └── README.md
```

## 🚀 环境准备与运行

### 1. 安装依赖

本项目主要依赖 `openai` SDK 来调用火山方舟大模型，以及 `PyYAML` 来解析 DSL 文件。

```bash
pip install openai pyyaml
```

### 2. 配置 API Key

本项目使用环境变量 `ARK_API_KEY` 来认证火山方舟大模型的 API 访问权限。您需要在运行程序前设置此变量。

+ **Windows (CMD/PowerShell):**

  ```Bash

  set ARK_API_KEY=YOUR_VOLCES_ARK_KEY
  # 或 (PowerShell)
  $env:ARK_API_KEY="YOUR_VOLCES_ARK_KEY"

  ```

+ **Linux/macOS (Bash):**

  ```Bash

  export ARK_API_KEY="YOUR_VOLCES_ARK_KEY"

  ```

  **注意：** 请将 `YOUR_VOLCES_ARK_KEY` 替换为您的实际 API 密钥。

### 3. 运行程序

在项目根目录下运行核心解释器：

```Bash

python interpreter_core.py

```