#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time
import random
import os
from datetime import datetime
from ml_analyzer import MLAnalyzer

class WeiboSpider:
    def __init__(self, output_dir="weibo_data"):
        """
        初始化微博爬虫
        
        参数:
        - output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化分析器
        self.analyzer = MLAnalyzer()
        
        # 设置请求头和Cookie
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://weibo.com/',
            'Connection': 'keep-alive',
            'Cookie': 'alf=02_1750516658; scf=AkWHOAHKVZR4U72tMy8Q9LgjIM7MQMvaHKSwQ04eOAsI2JBgQkQlmfrVVyedYcX4H4xf1lMZmepPJVFN3N841Ao.; SUB=_2A25FK0biDeRhGeFN4lcQ9CvOwjiIHXVmScYqrDV8PUNbmtAbLW_WkW9NQ6CKww8EwXECI8JlmiQpUQKXs8dpOdDq; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWeLWqEhZspcsieflC20plM5NHD95QNe0.feKBfeo.XWs4DqcjLPEH81F-ReE-RBEH8SCHWxbHF1CH8SFHFBE-4SEH8SE-4SF-4xntt; WBPSESS=W66fnaoZnYKPDz3Z3SHfiobUNR0t11ESD3A9xqxy8ehc3p8TkmgbC7FjmtozMmYK7QurYzSmlE6O2FLDqKVDAqh-oFLsCLR8CxSj2aBAfc71Qt-4PUU6Ve_iJBaTQAnP-qLHPOmuJ13HfRasQnf_zA==; XSRF-TOKEN=QXhEQujwl5E0gIA29udcRdhn'
        }
    
    def get_entertainment_weibo(self, page=1, count=20):
        """
        获取娱乐微博
        
        参数:
        - page: 页码
        - count: 每页数量
        
        返回:
        - 微博列表
        """
        try:
            # 娱乐超话ID
            entertainment_id = '1008084882401a015244fca5c97c97e6b4a94a'
            
            # 构建请求URL
            url = f'https://weibo.com/ajax/feed/hottimeline?containerid={entertainment_id}&page={page}&count={count}'
            
            # 发送请求
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # 解析响应
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok') == 1:
                    weibo_list = []
                    
                    for card in data.get('data', {}).get('cards', []):
                        if card.get('card_type') == 9:  # 微博类型
                            mblog = card.get('mblog', {})
                            
                            # 提取微博信息
                            weibo_id = mblog.get('id', '')
                            content = mblog.get('text', '')
                            
                            # 清理HTML标签
                            content = self.analyzer.preprocess_text(content)
                            
                            # 提取互动数据
                            reposts_count = mblog.get('reposts_count', 0)
                            comments_count = mblog.get('comments_count', 0)
                            attitudes_count = mblog.get('attitudes_count', 0)  # 点赞数
                            
                            # 判断是否有图片和视频
                            has_images = len(mblog.get('pic_ids', [])) > 0
                            has_videos = 'page_info' in mblog and mblog['page_info'].get('type') == 'video'
                            
                            # 构建微博数据
                            weibo_data = {
                                'weibo_id': weibo_id,
                                'content': content,
                                'forwards': reposts_count,
                                'comments': comments_count,
                                'likes': attitudes_count,
                                'has_images': has_images,
                                'has_videos': has_videos,
                                'created_at': mblog.get('created_at', ''),
                            }
                            
                            weibo_list.append(weibo_data)
                    
                    return weibo_list
                else:
                    print(f"获取微博失败: {data.get('msg', '未知错误')}")
            else:
                print(f"请求失败，状态码: {response.status_code}")
                
            return []
            
        except Exception as e:
            print(f"获取娱乐微博时出错: {e}")
            return []
    
    def crawl_and_analyze(self, pages=3, min_likes=500):
        """
        爬取并分析微博
        
        参数:
        - pages: 爬取的页数
        - min_likes: 最低点赞数，用于筛选
        
        返回:
        - 分析结果
        """
        all_weibos = []
        
        print(f"开始爬取 {pages} 页微博...")
        
        for page in range(1, pages + 1):
            print(f"正在爬取第 {page} 页...")
            
            # 获取微博
            weibo_list = self.get_entertainment_weibo(page=page)
            
            if weibo_list:
                all_weibos.extend(weibo_list)
                print(f"第 {page} 页获取到 {len(weibo_list)} 条微博")
            else:
                print(f"第 {page} 页未获取到微博")
            
            # 随机延迟，避免请求过快
            delay = random.uniform(1, 3)
            time.sleep(delay)
        
        print(f"共获取 {len(all_weibos)} 条微博")
        
        if not all_weibos:
            return {"error": "未获取到微博数据"}
        
        # 使用分析器进行分析
        analysis_result = self.analyzer.analyze_weibos(all_weibos, min_likes=min_likes)
        
        # 保存结果
        self._save_result(analysis_result)
        
        return analysis_result
    
    def _save_result(self, result):
        """保存分析结果"""
        if not result:
            return
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.output_dir, f'weibo_analysis_{timestamp}.json')
            
            # 保存为JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"分析结果已保存到 {filename}")
            
            # 提取并保存热门微博
            if 'filtered_weibos' in result:
                hot_weibos = result['filtered_weibos']
                
                if hot_weibos:
                    hot_filename = os.path.join(self.output_dir, f'hot_weibos_{timestamp}.json')
                    
                    with open(hot_filename, 'w', encoding='utf-8') as f:
                        json.dump(hot_weibos, f, ensure_ascii=False, indent=2)
                    
                    print(f"热门微博已保存到 {hot_filename}")
        
        except Exception as e:
            print(f"保存结果时出错: {e}")

# 示例用法
if __name__ == "__main__":
    # 初始化爬虫
    spider = WeiboSpider()
    
    # 爬取并分析微博（默认爬取3页，筛选点赞数≥500的微博）
    result = spider.crawl_and_analyze(pages=3, min_likes=500)
    
    # 打印分析结果概览
    if 'error' not in result:
        print("\n分析结果概览:")
        print(f"原始微博数: {result.get('original_count', 0)}")
        print(f"筛选后微博数: {result.get('filtered_count', 0)}")
        
        if 'trending_topics' in result and result['trending_topics']:
            print("\n热门话题:")
            for i, topic in enumerate(result['trending_topics'][:5], 1):
                print(f"{i}. {topic['keyword']} (热度分: {topic['score']:.2f})") 