#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速打开图片画廊脚本
"""

import os
import sys
import webbrowser
from datetime import datetime

def find_latest_gallery():
    """查找最新的图片画廊文件"""
    gallery_files = []
    
    # 查找所有画廊文件
    for file in os.listdir('.'):
        if file.startswith('simple_gallery_') and file.endswith('.html'):
            gallery_files.append(file)
    
    if gallery_files:
        # 返回最新的文件
        latest_file = sorted(gallery_files)[-1]
        return latest_file
    
    return None

def main():
    print("🎨 图片画廊快速访问工具")
    print("=" * 40)
    
    # 检查是否有现有的画廊文件
    latest_gallery = find_latest_gallery()
    
    if latest_gallery:
        print(f"📁 找到最新画廊: {latest_gallery}")
        
        # 询问是否使用现有文件还是重新生成
        choice = input("\n选择操作:\n1. 打开现有画廊\n2. 重新生成画廊\n请输入数字 (1/2): ").strip()
        
        if choice == "1":
            # 直接打开现有文件
            full_path = os.path.abspath(latest_gallery)
            print(f"\n🌐 正在打开: {full_path}")
            webbrowser.open(f'file://{full_path}')
            print("✅ 已在浏览器中打开图片画廊")
            return
        elif choice != "2":
            print("❌ 无效选择，退出")
            return
    
    # 生成新的画廊
    try:
        from create_simple_gallery import create_simple_gallery
        print("\n🔄 正在生成新的图片画廊...")
        html_file = create_simple_gallery()
        
        if html_file:
            full_path = os.path.abspath(html_file)
            print(f"\n✅ 画廊生成完成!")
            print(f"📁 文件位置: {html_file}")
            print(f"🔗 完整路径: {full_path}")
            
            # 自动打开
            print("\n🌐 正在打开画廊...")
            webbrowser.open(f'file://{full_path}')
            print("✅ 已在浏览器中打开图片画廊")
        else:
            print("❌ 画廊生成失败")
            
    except ImportError:
        print("❌ 未找到画廊生成器模块 (create_simple_gallery.py)")
    except Exception as e:
        print(f"❌ 生成画廊时出错: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}") 