import csv
import os
import time
from typing import Dict, Any, List, Optional

ACCOUNTS_FILE = "accounts.csv"
ORDERS_FILE = "orders.csv"
COMPLAINTS_FILE = "complaints.csv"
PRODUCTS_FILE = "products.csv"

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

    def query_order(self, order_id: str) -> Optional[Dict[str, str]]:
        """根据 order_id 查询订单信息。"""
        for order in self._data['orders']:
            if order.get('order_id') == order_id:
                return {
                    'status': order['status'],
                    'eta': order['eta'],
                    'product_name': order['product_name']
                }
        return None # 未找到订单
        
    def query_product(self, product_name: str) -> Optional[Dict[str, str]]:
        """ V2.1 新增：根据 product_name 查询商品信息。"""
        # 简单模糊匹配（将输入和记录都转小写再进行搜索）
        search_name_lower = product_name.lower()
        
        for product in self._data['products']:
            if search_name_lower in product.get('product_name', '').lower():
                # 返回完整的商品信息
                return product
        return None # 未找到商品
        
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
        
    def deactivate_account(self, account_id: str) -> bool:
        """模拟注销账户操作。"""
        initial_count = len(self._data['accounts'])
        self._data['accounts'] = [
            account for account in self._data['accounts'] 
            if account.get('account_id') != account_id
        ]
        if len(self._data['accounts']) < initial_count:
            self._save_csv(ACCOUNTS_FILE, self._data['accounts'])
            return True
        return False
