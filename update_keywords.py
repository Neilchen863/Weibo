#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import os

def update_keywords_from_classification():
    """
    从keyword and classification.txt文件读取关键词并更新到项目中
    """
    # 读取分类文件
    classification_file = "keyword and classification.txt"
    
    try:
        # 读取CSV文件
        df = pd.read_csv(classification_file, encoding='utf-8')
        
        # 提取第一列的关键词
        keywords = df.iloc[:, 0].dropna().unique().tolist()
        
        print(f"从分类文件中读取到 {len(keywords)} 个唯一关键词")
        
        # 显示前10个关键词作为预览
        print("前10个关键词:")
        for i, keyword in enumerate(keywords[:10]):
            print(f"{i+1}. {keyword}")
        
        # 保存到keywords.txt
        with open('keywords.txt', 'w', encoding='utf-8') as f:
            for keyword in keywords:
                f.write(f"{keyword}\n")
        
        print(f"\n关键词已成功更新到 keywords.txt 文件")
        print(f"总共 {len(keywords)} 个关键词")
        
        return keywords
        
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return []

if __name__ == "__main__":
    update_keywords_from_classification() 