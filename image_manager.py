#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片管理工具
提供图片搜索、查看和管理功能
"""

import os
import json
import pandas as pd
import shutil
from datetime import datetime
import argparse
import webbrowser

class ImageManager:
    def __init__(self):
        self.media_dir = 'media'
        self.results_dir = 'results'
        self.df = None
        self.load_latest_results()
    
    def load_latest_results(self):
        """加载最新的结果文件"""
        try:
            result_files = [f for f in os.listdir(self.results_dir) 
                          if f.startswith('all_results_') and f.endswith('.csv')]
            if result_files:
                latest_result = sorted(result_files)[-1]
                result_path = os.path.join(self.results_dir, latest_result)
                self.df = pd.read_csv(result_path)
                print(f"已加载结果文件: {latest_result}")
            else:
                print("未找到结果文件")
        except Exception as e:
            print(f"加载结果文件时出错: {e}")
    
    def get_statistics(self):
        """获取图片统计信息"""
        if not os.path.exists(self.media_dir):
            return {}
        
        stats = {}
        total_images = 0
        total_size = 0
        
        for keyword_dir in os.listdir(self.media_dir):
            keyword_path = os.path.join(self.media_dir, keyword_dir)
            if not os.path.isdir(keyword_path):
                continue
            
            image_count = 0
            keyword_size = 0
            
            for image_file in os.listdir(keyword_path):
                if image_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    image_path = os.path.join(keyword_path, image_file)
                    file_size = os.path.getsize(image_path)
                    image_count += 1
                    keyword_size += file_size
                    total_size += file_size
            
            total_images += image_count
            stats[keyword_dir] = {
                'image_count': image_count,
                'size_mb': round(keyword_size / (1024 * 1024), 2)
            }
        
        stats['_total'] = {
            'total_images': total_images,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
        
        return stats

def main():
    parser = argparse.ArgumentParser(description='图片管理工具')
    parser.add_argument('--stats', '-s', action='store_true', help='显示统计信息')
    
    args = parser.parse_args()
    
    manager = ImageManager()
    
    if args.stats:
        stats = manager.get_statistics()
        print("\n=== 图片统计信息 ===")
        for keyword, data in stats.items():
            if keyword == '_total':
                print(f"\n总计: {data['total_images']} 张图片, {data['total_size_mb']} MB")
            else:
                print(f"{keyword}: {data['image_count']} 张图片, {data['size_mb']} MB")
        return

if __name__ == "__main__":
    main() 