#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fetch import WeiboSpider
from keyword_manager import KeywordManager
from ml_analyzer import MLAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weibo_spider.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def load_config():
    """加载配置文件"""
    config_file = "config.json"
    default_config = {
        "cookie": "",
        "default_pages": 5,
        "min_score": 80,
        "min_likes": 500,  # 添加最低点赞数参数
        "download_media": False,
        "max_retries": 3,
        "retry_delay": 5,
        "thread_pool_size": 4,
        "proxy": None
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 确保所有必要的配置项都存在
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
        else:
            config = default_config
            # 保存默认配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        
        return config
    except Exception as e:
        logging.error(f"加载配置文件时出错: {e}")
        return default_config

def save_config(config):
    """保存配置到文件"""
    try:
        with open("config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"保存配置文件时出错: {e}")

def process_keyword(keyword, spider, ml_analyzer, config, now):
    """处理单个关键词的爬取和分析"""
    try:
        logging.info(f"开始搜索关键词: {keyword}")
        
        # 获取搜索结果
        results = spider.search_keyword(
            keyword, 
            pages=config["default_pages"], 
            start_page=config["start_page"],
            download_media=config["download_media"]
        )
        
        if not results:
            logging.warning(f"未找到关键词 '{keyword}' 的相关微博")
            return None
        
        logging.info(f"获取到 {len(results)} 条微博")
        
        # 应用机器学习分析
        logging.info("正在进行机器学习分析...")
        analysis_result = ml_analyzer.analyze_weibos(
            results, 
            min_score=config["min_score"],
            min_likes=config["min_likes"],  # 传递最低点赞数参数
            min_comments=config["min_comments"] if "min_comments" in config else 0,
            min_forwards=config["min_forwards"] if "min_forwards" in config else 0
        )
        
        if not analysis_result or "filtered_weibos" not in analysis_result:
            logging.warning(f"机器学习分析未返回有效结果")
            return None
        
        filtered_results = analysis_result["filtered_weibos"]
        logging.info(f"机器学习分析后保留 {len(filtered_results)} 条高质量微博")
        
        # 保存结果
        result_dir = "results"
        os.makedirs(result_dir, exist_ok=True)
        
        # 保存过滤后的微博数据
        df = pd.DataFrame(filtered_results)
        keyword_file = f"{result_dir}/{keyword}_{now}.csv"
        df.to_csv(keyword_file, index=False, encoding='utf-8-sig')
        logging.info(f"已保存过滤后的结果到 {keyword_file}")
        
        # 保存分析结果
        analysis_file = f"{result_dir}/{keyword}_analysis_{now}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        logging.info(f"已保存分析结果到 {analysis_file}")
        
        # 输出热门话题
        if "trending_topics" in analysis_result:
            logging.info("\n热门话题:")
            for topic in analysis_result["trending_topics"]:
                logging.info(f"- {topic['keyword']} (热度: {topic['score']:.2f}, 相关微博数: {topic['weibo_count']})")
        
        return filtered_results
        
    except Exception as e:
        logging.error(f"处理关键词 '{keyword}' 时出错: {e}")
        return None

def main():
    try:
        # 加载配置
        config = load_config()
        
        # 创建结果目录
        result_dir = "results"
        os.makedirs(result_dir, exist_ok=True)
        
        # 创建关键词管理器
        keyword_manager = KeywordManager()
        
        # 从文件加载关键词
        keywords = keyword_manager.load_from_file()
        
        # 如果没有关键词，使用默认的示例关键词
        if not keywords:
            logging.warning("未找到关键词文件或文件为空，使用示例关键词")
            keywords = [
                "示例关键词1",
                "示例关键词2",
                "示例关键词3",
            ]
            # 保存示例关键词到文件
            keyword_manager.add_keywords(keywords)
            keyword_manager.save_to_file()
        
        # 当前时间，用于文件命名
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建爬虫实例
        spider = WeiboSpider()
        
        # 设置代理（如果配置了的话）
        if config["proxy"]:
            spider.set_proxy(config["proxy"])
        
        # 使用配置文件中的Cookie
        if config["cookie"]:
            spider.set_cookies(config["cookie"])
            logging.info("已从配置文件加载Cookie")
        # else:
        #     # 如果没有配置Cookie，提示用户输入
        #     cookie_str = input("请输入微博Cookie（可选，提高爬取成功率）: ")
        #     if cookie_str:
        #         spider.set_cookies(cookie_str)
        #         # 保存Cookie到配置文件
        #         config["cookie"] = cookie_str
        #         save_config(config)
        
        # 提示用户输入最低点赞数
        try:
            # 使用配置文件中的值，而不是硬编码
            min_likes = config['min_likes']
            logging.info(f"使用配置文件中的最低点赞数阈值: {min_likes}")
        except ValueError:
            logging.warning(f"配置无效，使用默认值{config['min_likes']}")
            min_likes = config['min_likes']
        
        logging.info(f"筛选逻辑: 只保留点赞数 >= {min_likes} 的微博，并对这些微博进行综合评分和排序")
        
        # 创建机器学习分析器实例
        logging.info("正在初始化机器学习分析器...")
        ml_analyzer = MLAnalyzer()
        logging.info("机器学习分析器初始化完成")
        
        # 使用线程池处理关键词
        all_results = []
        with ThreadPoolExecutor(max_workers=config["thread_pool_size"]) as executor:
            # 提交所有任务
            future_to_keyword = {
                executor.submit(process_keyword, keyword, spider, ml_analyzer, config, now): keyword 
                for keyword in keywords
            }
            
            # 收集结果
            for future in future_to_keyword:
                keyword = future_to_keyword[future]
                try:
                    results = future.result()
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    logging.error(f"处理关键词 '{keyword}' 时出错: {e}")
        
        # 保存所有结果到一个合并文件
        if all_results:
            df_all = pd.DataFrame(all_results)
            all_file = f"{result_dir}/all_results_{now}.csv"
            df_all.to_csv(all_file, index=False, encoding='utf-8-sig')
            logging.info(f"\n已保存所有结果到 {all_file}")
            logging.info(f"总共获取到 {len(all_results)} 条高质量微博")
        
    except Exception as e:
        logging.error(f"程序运行出错: {e}")
        raise

if __name__ == "__main__":
    main()
