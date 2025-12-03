# data_manager.py

import csv
import os
import time
from typing import Dict, Any, List, Optional

ACCOUNTS_FILE = "accounts.csv"
ORDERS_FILE = "orders.csv"
COMPLAINTS_FILE = "complaints.csv"

class DataManager:
    """
    负责加载、查询和模拟更新项目中的 CSV 数据。
    """
    def __init__(self):
        self._data: Dict[str, List[Dict[str, str]]] = {
            'accounts': self._load_csv(ACCOUNTS_FILE),
            'orders': self._load_csv(ORDERS_FILE),
            'complaints': self._load_csv(COMPLAINTS_FILE)
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
        # 查找匹配的订单
        for order in self._data['orders']:
            if order.get('order_id') == order_id:
                # 返回订单状态和预计到达时间
                return {
                    'status': order['status'],
                    'eta': order['eta'],
                    'product_name': order['product_name']
                }
        return None # 未找到订单

    def submit_complaint(self, account_id: str, issue_description: str) -> Dict[str, Any]:
        """模拟提交投诉记录，并分配新的投诉编号。"""

        new_ref_id = f"C{int(time.time())}"
        
        # 构造新的投诉记录
        new_complaint = {
            'ref_id': new_ref_id,
            'account_id': account_id if account_id else "Guest", # 如果账户ID为空，则使用“访客”
            'issue_description': issue_description
        }
        
        # 将新记录添加到内存和文件中
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
                    # 验证旧密码正确，执行修改
                    account['password'] = new_password
                    success = True
                    break
                else:
                    # 旧密码不匹配
                    success = False
                    break

        if success:
            # 成功修改，写回文件 (模拟持久化)
            self._save_csv(ACCOUNTS_FILE, self._data['accounts'])
            return True
        
        # 如果账户不存在或密码不匹配，返回 False
        return False
        
    def deactivate_account(self, account_id: str) -> bool:
        """模拟注销账户操作 (这里只是移除账户或标记状态)。"""
        
        initial_count = len(self._data['accounts'])
        
        # 移除账户，并过滤掉匹配的 account_id
        self._data['accounts'] = [
            account for account in self._data['accounts'] 
            if account.get('account_id') != account_id
        ]
        
        # 检查是否有账户被移除
        if len(self._data['accounts']) < initial_count:
            # 账户被移除，写回文件
            self._save_csv(ACCOUNTS_FILE, self._data['accounts'])
            return True
        
        # 未找到该账户
        return False

if __name__ == '__main__':
    # 简单的测试演示
    dm = DataManager()
    
    # 测试查询
    order_info = dm.query_order("O20240901")
    print(f"\n[测试查询订单 O20240901]: {order_info}")
    
    # 测试投诉
    complaint_ref = dm.submit_complaint(account_id="user1002", issue_description="物流太慢")
    print(f"\n[测试提交投诉]: {complaint_ref}")
    
    # 测试修改密码 (失败：旧密码错误)
    change_fail = dm.change_password(account_id="user1001", old_password="wrong", new_password="new_pass")
    print(f"\n[测试修改密码-失败]: {change_fail}")
    
    # 测试修改密码 (成功)
    change_success = dm.change_password(account_id="user1001", old_password="pa$$word1", new_password="new_pass_OK")
    print(f"[测试修改密码-成功]: {change_success}")
    
    # 验证新密码是否写入
    print(f"[验证新密码]: {dm._data['accounts'][0]}")
    
    # 测试注销账户
    deactivate_success = dm.deactivate_account("test_acc")
    print(f"\n[测试注销账户-成功]: {deactivate_success}")
    # 验证账户是否移除
    print(f"[验证账户数量]: 剩余 {len(dm._data['accounts'])} 个账户。")