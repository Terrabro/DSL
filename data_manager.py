import csv
import os
import time
from typing import Dict, Any, List, Optional

ACCOUNTS_FILE = "./data/accounts.csv"
ORDERS_FILE = "./data/orders.csv"
COMPLAINTS_FILE = "./data/complaints.csv"
PRODUCTS_FILE = "./data/products.csv"

class DataManager:
    """
    负责加载、查询和模拟更新项目中的 CSV 数据。
    """
    def __init__(self):
        self._data: Dict[str, List[Dict[str, str]]] = {
            'accounts': self._load_csv(ACCOUNTS_FILE),
            'orders': self._load_csv(ORDERS_FILE),
            'complaints': self._load_csv(COMPLAINTS_FILE),
            'products': self._load_csv(PRODUCTS_FILE)
        }
        print("--- DataManager: CSV 数据加载完成 ---")

    def _load_csv(self, file_path: str) -> List[Dict[str, str]]:
        """从 CSV 文件加载数据到内存中。"""
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
        """将数据写回 CSV 文件 (用于模拟持久化)。"""
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

    # --- DSL 核心动作函数 ---

    def query_order(self, order_id: str) -> Optional[Dict[str, str]]:
        """根据 order_id 查询订单信息。"""
        for order in self._data['orders']:
            # 兼容性匹配：移除订单号中的空格或尝试进行简单匹配
            if order.get('order_id', '').strip() == order_id.strip():
                return {
                    'status': order['status'],
                    'eta': order['eta'],
                    'product_name': order['product_name']
                }
        return None

    def query_product(self, product_name: str) -> Optional[Dict[str, str]]:
        """根据 product_name 查询商品信息。"""
        search_name_lower = product_name.lower()
        
        for product in self._data['products']:
            if search_name_lower in product.get('product_name', '').lower():
                return product
        return None

    def submit_complaint(self, account_id: str, issue_description: str) -> Dict[str, Any]:
        """模拟提交投诉记录。"""
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
        """模拟修改账户密码。"""
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
        """模拟注销账户。"""
        found_and_matched = False
        
        for account in self._data['accounts']:
            if account.get('account_id') == account_id:
                if account.get('password') == old_password:
                    found_and_matched = True
                break

        if found_and_matched:
            # 移除账户
            self._data['accounts'] = [
                account for account in self._data['accounts'] 
                if account.get('account_id') != account_id
            ]
            self._save_csv(ACCOUNTS_FILE, self._data['accounts'])
            return True
        
        return False