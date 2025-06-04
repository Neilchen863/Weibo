#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd

def select_celebrity_keywords():
    """
    只选择分类为celebrity的关键词
    """
    # 读取分类文件
    classification_file = "keyword and classification.txt"
    
    try:
        # 读取CSV文件
        df = pd.read_csv(classification_file, encoding='utf-8')
        
        # 只选择celebrity分类的关键词
        celebrity_keywords = df[df.iloc[:, 1] == 'celebrity'].iloc[:, 0].tolist()
        
        print(f"找到 {len(celebrity_keywords)} 个名人关键词:")
        for i, keyword in enumerate(celebrity_keywords):
            print(f"{i+1}. {keyword}")
        
        # 保存到keywords.txt
        with open('keywords.txt', 'w', encoding='utf-8') as f:
            for keyword in celebrity_keywords:
                f.write(f"{keyword}\n")
        
        print(f"\n已更新为 {len(celebrity_keywords)} 个名人关键词")
        
        return celebrity_keywords
        
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return []

if __name__ == "__main__":
    select_celebrity_keywords() 