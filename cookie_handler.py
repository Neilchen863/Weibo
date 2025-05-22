#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import time
from datetime import datetime

class CookieHandler:
    def __init__(self, cookie_file='cookies.json'):
        """
        初始化Cookie处理器
        
        参数:
        - cookie_file: Cookie文件路径
        """
        self.cookie_file = cookie_file
        self.cookies = self._load_cookies()
        
    def _load_cookies(self):
        """从文件加载Cookie"""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载Cookie文件出错: {e}")
                return {}
        return {}
    
    def save_cookies(self):
        """保存Cookie到文件"""
        try:
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(self.cookies, f, ensure_ascii=False, indent=2)
            print(f"Cookie已保存到 {self.cookie_file}")
        except Exception as e:
            print(f"保存Cookie出错: {e}")
    
    def update_cookies(self, cookie_dict):
        """更新Cookie"""
        if not cookie_dict:
            return
        
        # 添加更新时间
        cookie_dict['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 更新Cookie
        self.cookies.update(cookie_dict)
        
        # 保存Cookie
        self.save_cookies()
    
    def get_cookie_dict(self):
        """获取Cookie字典，用于requests请求"""
        # 移除非Cookie字段
        cookie_dict = {k: v for k, v in self.cookies.items() if k != 'update_time'}
        return cookie_dict
    
    def get_cookie_string(self):
        """获取Cookie字符串，用于请求头"""
        cookie_dict = self.get_cookie_dict()
        return '; '.join([f'{k}={v}' for k, v in cookie_dict.items()])
    
    def is_expired(self, expire_days=1):
        """检查Cookie是否过期"""
        if 'update_time' not in self.cookies:
            return True
        
        try:
            update_time = datetime.strptime(self.cookies['update_time'], '%Y-%m-%d %H:%M:%S')
            current_time = datetime.now()
            
            # 计算时间差
            time_diff = (current_time - update_time).total_seconds() / 86400  # 转换为天
            
            return time_diff > expire_days
        except Exception as e:
            print(f"检查Cookie过期时出错: {e}")
            return True

# 示例用法
if __name__ == "__main__":
    # 初始化Cookie处理器
    cookie_handler = CookieHandler()
    
    # 使用用户提供的Cookie值
    cookie_dict = {
        'alf': '02_1750516658',
        'scf': 'AkWHOAHKVZR4U72tMy8Q9LgjIM7MQMvaHKSwQ04eOAsI2JBgQkQlmfrVVyedYcX4H4xf1lMZmepPJVFN3N841Ao.',
        'SUB': '_2A25FK0biDeRhGeFN4lcQ9CvOwjiIHXVmScYqrDV8PUNbmtAbLW_WkW9NQ6CKww8EwXECI8JlmiQpUQKXs8dpOdDq',
        'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9WWeLWqEhZspcsieflC20plM5NHD95QNe0.feKBfeo.XWs4DqcjLPEH81F-ReE-RBEH8SCHWxbHF1CH8SFHFBE-4SEH8SE-4SF-4xntt',
        'WBPSESS': 'W66fnaoZnYKPDz3Z3SHfiobUNR0t11ESD3A9xqxy8ehc3p8TkmgbC7FjmtozMmYK7QurYzSmlE6O2FLDqKVDAqh-oFLsCLR8CxSj2aBAfc71Qt-4PUU6Ve_iJBaTQAnP-qLHPOmuJ13HfRasQnf_zA==',
        'XSRF-TOKEN': 'QXhEQujwl5E0gIA29udcRdhn'
    }
    
    # 更新Cookie
    cookie_handler.update_cookies(cookie_dict)
    
    # 获取Cookie字符串
    cookie_string = cookie_handler.get_cookie_string()
    print(f"Cookie字符串: {cookie_string}")
    
    # 获取Cookie字典
    cookie_dict = cookie_handler.get_cookie_dict()
    print(f"Cookie字典: {cookie_dict}") 