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
import time
import base64
from PIL import Image
import io

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

def image_to_base64(image_path, max_size=(300, 300)):
    """
    将图片转换为Base64编码字符串
    
    参数:
    - image_path: 图片文件路径
    - max_size: 最大尺寸(宽, 高)，用于压缩图片
    
    返回:
    - Base64编码字符串
    """
    try:
        if not os.path.exists(image_path):
            return ""
        
        # 打开图片并调整大小以减少文件大小
        with Image.open(image_path) as img:
            # 转换为RGB（如果是RGBA等格式）
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # 计算缩放比例，保持长宽比
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 将图片保存到内存中
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)
            
            # 转换为Base64
            image_data = buffer.getvalue()
            base64_string = base64.b64encode(image_data).decode('utf-8')
            
            return f"data:image/jpeg;base64,{base64_string}"
    
    except Exception as e:
        logging.warning(f"转换图片到Base64时出错 {image_path}: {e}")
        return ""

def add_image_data_to_weibos(weibos):
    """
    为微博数据添加图片的Base64编码
    
    参数:
    - weibos: 微博数据列表
    
    返回:
    - 包含图片数据的微博列表
    """
    for weibo in weibos:
        image_paths = weibo.get('image_paths', '')
        base64_images = []
        
        if image_paths:
            paths = image_paths.split('|')
            for path in paths:
                if path and os.path.exists(path):
                    base64_data = image_to_base64(path)
                    if base64_data:
                        base64_images.append(base64_data)
        
        # 添加Base64图片数据到微博信息中
        weibo['image_base64'] = '|'.join(base64_images) if base64_images else ''
        weibo['image_count'] = len(base64_images)
    
    return weibos

def download_filtered_media(spider, filtered_weibos, keyword):
    """
    为通过筛选的高质量微博下载图片
    
    参数:
    - spider: 爬虫实例
    - filtered_weibos: 筛选后的微博列表
    - keyword: 关键词
    """
    downloaded_count = 0
    for weibo in filtered_weibos:
        if weibo.get('has_images', False):
            image_urls = weibo.get('image_urls', '').split('|')
            image_paths = []
            
            for url in image_urls:
                if url:
                    local_path = spider.download_media(url, 'image', keyword, weibo['weibo_id'])
                    if local_path:
                        image_paths.append(local_path)
                        downloaded_count += 1
                    time.sleep(0.5)  # 避免请求过快
            
            # 更新微博数据中的本地路径信息
            weibo['image_paths'] = '|'.join(image_paths)
    
    return downloaded_count

def process_keyword(keyword, spider, ml_analyzer, config, now, keyword_to_type):
    """处理单个关键词的爬取和分析"""
    try:
        logging.info(f"开始搜索关键词: {keyword}")
        
        # 获取关键词的分类
        keyword_type = keyword_to_type.get(keyword, "unknown")
        logging.info(f"关键词 '{keyword}' 的分类: {keyword_type}")
        
        # 获取搜索结果 - 暂时关闭媒体下载
        results = spider.search_keyword(
            keyword, 
            pages=config["default_pages"], 
            start_page=config["start_page"],
            download_media=False  # 先不下载，等筛选后再下载
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
        
        # 为每条微博添加关键词分类信息
        for weibo in filtered_results:
            weibo['type'] = keyword_type
        
        # 如果启用了媒体下载，为筛选后的微博下载图片
        if config["download_media"]:
            logging.info(f"开始为 {keyword} 的高质量微博下载图片...")
            downloaded_count = download_filtered_media(spider, filtered_results, keyword)
            logging.info(f"为关键词 '{keyword}' 下载了 {downloaded_count} 张图片")
        
        # 添加图片Base64数据到微博中
        if config["download_media"]:
            logging.info(f"正在处理图片数据...")
            filtered_results = add_image_data_to_weibos(filtered_results)
            logging.info(f"图片数据处理完成")
        
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

def load_keyword_classifications():
    """
    加载关键词分类信息
    
    返回:
    - 关键词到分类的映射字典
    """
    classification_file = "keyword and classification.txt"
    keyword_to_type = {}
    
    try:
        if os.path.exists(classification_file):
            df = pd.read_csv(classification_file, encoding='utf-8')
            # 创建关键词到分类的映射
            for _, row in df.iterrows():
                keyword = row.iloc[0]  # 第一列是关键词
                classification = row.iloc[1]  # 第二列是分类
                keyword_to_type[keyword] = classification
            
            logging.info(f"成功加载 {len(keyword_to_type)} 个关键词分类")
        else:
            logging.warning(f"分类文件 {classification_file} 不存在")
    
    except Exception as e:
        logging.error(f"加载关键词分类时出错: {e}")
    
    return keyword_to_type

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
        
        # 加载关键词分类信息
        keyword_to_type = load_keyword_classifications()
        
        # 使用线程池处理关键词
        all_results = []
        with ThreadPoolExecutor(max_workers=config["thread_pool_size"]) as executor:
            # 提交所有任务
            future_to_keyword = {
                executor.submit(process_keyword, keyword, spider, ml_analyzer, config, now, keyword_to_type): keyword 
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
