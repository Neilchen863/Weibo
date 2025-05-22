#!/usr/bin/env python
# -*- coding: utf-8 -*-

from keyword_manager import KeywordManager

def main():
    print("=== 微博关键词管理工具 ===")
    
    # 创建关键词管理器
    manager = KeywordManager()
    
    # 加载现有关键词
    existing_keywords = manager.load_from_file()
    
    # 显示现有关键词
    if existing_keywords:
        print("\n当前关键词列表:")
        for i, keyword in enumerate(existing_keywords, 1):
            print(f"{i}. {keyword}")
    else:
        print("\n当前没有关键词")
    
    # 菜单循环
    while True:
        print("\n请选择操作:")
        print("1. 添加单个关键词\n add keyword")
        print("2. 批量添加关键词\n add keywords")
        print("3. 从文件导入关键词\n import keywords from file")
        print("4. 删除关键词\n delete keyword")
        print("5. 导出关键词到Excel\n export keywords to excel")
        print("6. 查看当前关键词列表\n view current keywords list")
        print("0. 保存并退出\n save and exit")
        
        choice = input("\n请输入选项编号: ")
        
        if choice == "1":
            # 添加单个关键词
            keyword = input("请输入要添加的关键词: ")
            manager.add_keyword(keyword)
            
        elif choice == "2":
            # 批量添加关键词
            print("请输入要添加的关键词，每行一个，输入空行结束:")
            keywords = []
            while True:
                line = input()
                if not line:
                    break
                keywords.append(line)
            
            added = manager.add_keywords(keywords)
            print(f"成功添加 {added} 个新关键词")
            
        elif choice == "3":
            # 从文件导入关键词
            file_path = input("请输入关键词文件路径: ")
            if file_path:
                new_keywords = manager.load_from_file(file_path)
                added = manager.add_keywords(new_keywords)
                print(f"从文件导入并添加了 {added} 个新关键词")
            
        elif choice == "4":
            # 删除关键词
            if not manager.keywords:
                print("没有关键词可删除")
                continue
                
            print("\n当前关键词列表:")
            for i, keyword in enumerate(manager.keywords, 1):
                print(f"{i}. {keyword}")
                
            index = input("\n请输入要删除的关键词编号，或直接输入关键词: ")
            try:
                idx = int(index) - 1
                if 0 <= idx < len(manager.keywords):
                    keyword = manager.keywords[idx]
                    manager.remove_keyword(keyword)
                else:
                    print("编号无效")
            except ValueError:
                # 如果输入的不是数字，则认为是直接输入的关键词
                manager.remove_keyword(index)
            
        elif choice == "5":
            # 导出到Excel
            manager.export_to_excel()
            
        elif choice == "6":
            # 查看当前关键词列表
            if manager.keywords:
                print("\n当前关键词列表:")
                for i, keyword in enumerate(manager.keywords, 1):
                    print(f"{i}. {keyword}")
            else:
                print("\n当前没有关键词")
            
        elif choice == "0":
            # 保存并退出
            manager.save_to_file()
            print("关键词已保存，程序退出")
            break
            
        else:
            print("选项无效，请重新输入")

if __name__ == "__main__":
    main() 