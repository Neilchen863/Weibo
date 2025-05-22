#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
from datetime import datetime

class KeywordManager:
    def __init__(self):
        self.keywords = []
        self.keyword_file = "keywords.txt"
    
    def load_from_file(self, file_path=None):
        """
        从文件加载关键词
        
        参数:
        - file_path: 关键词文件路径，默认为keywords.txt
        
        返回:
        - 关键词列表
        """
        target_file = file_path or self.keyword_file
        
        if not os.path.exists(target_file):
            print(f"关键词文件 {target_file} 不存在")
            return []
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                # 读取所有行并去除空白字符
                keywords = [line.strip() for line in f.readlines() if line.strip()]
            
            print(f"从文件 {target_file} 成功加载 {len(keywords)} 个关键词")
            self.keywords = keywords
            return keywords
        except Exception as e:
            print(f"加载关键词文件时出错: {e}")
            return []
    
    def save_to_file(self, keywords=None, file_path=None):
        """
        保存关键词到文件
        
        参数:
        - keywords: 要保存的关键词列表，默认使用当前加载的关键词
        - file_path: 保存文件路径，默认为keywords.txt
        """
        target_file = file_path or self.keyword_file
        kw_list = keywords or self.keywords
        
        if not kw_list:
            print("没有关键词可保存")
            return False
        
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                for keyword in kw_list:
                    f.write(f"{keyword}\n")
            
            print(f"成功将 {len(kw_list)} 个关键词保存到文件 {target_file}")
            return True
        except Exception as e:
            print(f"保存关键词到文件时出错: {e}")
            return False
    
    def add_keyword(self, keyword):
        """
        添加单个关键词
        
        参数:
        - keyword: 要添加的关键词
        """
        keyword = keyword.strip()
        if not keyword:
            return False
        
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            print(f"已添加关键词: {keyword}")
            return True
        else:
            print(f"关键词 '{keyword}' 已存在")
            return False
    
    def add_keywords(self, keywords):
        """
        批量添加关键词
        
        参数:
        - keywords: 关键词列表
        """
        added_count = 0
        for keyword in keywords:
            if self.add_keyword(keyword):
                added_count += 1
        
        print(f"成功添加 {added_count} 个新关键词")
        return added_count
    
    def remove_keyword(self, keyword):
        """
        删除单个关键词
        
        参数:
        - keyword: 要删除的关键词
        """
        if keyword in self.keywords:
            self.keywords.remove(keyword)
            print(f"已删除关键词: {keyword}")
            return True
        else:
            print(f"关键词 '{keyword}' 不存在")
            return False
    
    def export_to_excel(self, file_path=None):
        """
        将关键词导出为Excel文件
        
        参数:
        - file_path: 导出文件路径，默认为keywords_年月日_时分秒.xlsx
        """
        if not self.keywords:
            print("没有关键词可导出")
            return False
        
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_file = file_path or f"keywords_{now}.xlsx"
        
        try:
            # 创建DataFrame
            df = pd.DataFrame({"关键词": self.keywords})
            
            # 导出到Excel
            df.to_excel(target_file, index=False)
            
            print(f"成功将 {len(self.keywords)} 个关键词导出到文件 {target_file}")
            return True
        except Exception as e:
            print(f"导出关键词到Excel时出错: {e}")
            return False 