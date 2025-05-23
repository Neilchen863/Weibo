#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import time
import random
import requests
import os
from lxml import etree
from tqdm import tqdm
from fake_useragent import UserAgent

class WeiboSpider:
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://s.weibo.com/weibo"
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        
        # 可选：设置Cookie以提高爬取效果
        self.cookies = {}
        
        # 创建下载目录 (保留但不会使用)
        self.media_dir = "media"
        os.makedirs(self.media_dir, exist_ok=True)
    
    def _get_random_delay(self):
        """生成随机延迟，避免被检测为爬虫"""
        return random.uniform(1, 3)
    
    def _update_headers(self):
        """更新请求头，防止被检测"""
        self.headers["User-Agent"] = self.ua.random
    
    # 以下媒体下载函数保留但在简化版中不会被调用
    def download_media(self, url, media_type, keyword, weibo_id):
        """
        下载媒体文件（图片或视频）- 简化版中不会使用此功能
        """
        return ""
    
    def extract_images(self, card, keyword, weibo_id):
        """
        提取微博图片链接 - 简化版中不会下载
        """
        # 图片容器通常在这些位置
        image_nodes = card.xpath('.//div[contains(@class, "media-pic")]//img/@src')
        
        # 有时候图片在另一个容器里
        if not image_nodes:
            image_nodes = card.xpath('.//div[@node-type="feed_list_media_prev"]//img/@src')
        
        # 清理URL地址
        image_urls = []
        for url in image_nodes:
            if url.startswith('//'):
                url = 'https:' + url
            
            # 将thumbnail链接转换为原图链接
            if '/thumb150/' in url:
                url = url.replace('/thumb150/', '/large/')
            
            image_urls.append(url)
        
        return image_urls, []  # 返回空列表作为本地路径，不下载
    
    def extract_videos(self, card, keyword, weibo_id):
        """
        提取微博视频链接 - 简化版中不会下载
        """
        # 找视频链接的容器
        video_nodes = card.xpath('.//div[contains(@class, "media-video")]')
        
        video_urls = []
        for node in video_nodes:
            video_url = node.xpath('./@data-url')
            if not video_url:
                # 尝试其他可能的属性
                video_url = node.xpath('./video/@src') or node.xpath('./@action-data')
            
            if video_url:
                url = video_url[0]
                if url.startswith('//'):
                    url = 'https:' + url
                
                video_urls.append(url)
        
        return video_urls, []  # 返回空列表作为本地路径，不下载
    
    def search_keyword(self, keyword, pages, start_page=1, download_media=False):
        """
        根据关键词搜索微博
        
        参数:
        - keyword: 搜索关键词
        - pages: 爬取页数，默认5页
        - start_page: 开始爬取的页码，默认从第1页开始
        - download_media: 媒体下载标志(简化版中忽略此参数)
        
        返回:
        - 搜索结果列表
        """
        results = []
        self.download_media_enabled = False  # 强制关闭媒体下载
        
        end_page = start_page + pages - 1
        print(f"准备搜索关键词: {keyword}, 计划爬取 {start_page} 到 {end_page} 页")
        
        for page in tqdm(range(start_page, end_page + 1), desc="爬取进度"):
            try:
                # 构建搜索URL
                search_url = f"{self.base_url}?q={keyword}&typeall=1&suball=1&timescope=custom:&page={page}"
                
                # 更新请求头
                self._update_headers()
                
                # 发送请求
                response = requests.get(
                    search_url, 
                    headers=self.headers, 
                    cookies=self.cookies, 
                    timeout=10
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    print(f"请求失败，状态码: {response.status_code}")
                    continue
                
                # 解析页面
                html = etree.HTML(response.text)
                
                # 提取微博列表
                weibo_cards = html.xpath('//div[@class="card-wrap"]')
                
                if not weibo_cards:
                    print(f"页面 {page} 未找到微博卡片，可能需要登录或更换Cookie")
                    continue
                
                # 解析每条微博
                for card in weibo_cards:
                    try:
                        # 排除广告或其他非微博内容
                        if not card.xpath('.//div[@class="content"]'):
                            continue
                        
                        # 提取微博ID
                        weibo_id = card.xpath('.//div[@class="from"]/a[1]/@href')
                        weibo_id = weibo_id[0].split('/')[-1] if weibo_id else "未知ID"
                        
                        # 提取用户信息
                        user_name = card.xpath('.//a[@class="name"]/text()')
                        user_name = user_name[0] if user_name else "未知用户"
                        
                        user_link = card.xpath('.//a[@class="name"]/@href')
                        user_link = f"https:{user_link[0]}" if user_link else ""
                        
                        # 提取微博内容
                        content_elements = card.xpath('.//p[@class="txt" or @node-type="feed_list_content_full"]')
                        content = content_elements[0].xpath('string(.)').strip() if content_elements else "无内容"
                        
                        # 提取发布时间
                        publish_time = card.xpath('.//div[@class="from"]/a[1]/text()')
                        publish_time = publish_time[0].strip() if publish_time else "未知时间"
                        
                        # 提取互动数据
                        forwards = card.xpath('.//div[@class="card-act"]/ul/li[2]//text()')
                        forwards = ''.join(forwards).strip().replace('转发', '') or '0'
                        if '万' in forwards:
                            forwards = float(forwards.replace('万', '')) * 10000
                        
                        comments = card.xpath('.//div[@class="card-act"]/ul/li[3]//text()')
                        comments = ''.join(comments).strip().replace('评论', '') or '0'
                        if '万' in comments:
                            comments = float(comments.replace('万', '')) * 10000
                        
                        likes = card.xpath('.//div[@class="card-act"]/ul/li[4]/a/em/text()')
                        likes = likes[0] if likes else '0'
                        if '万' in likes:
                            likes = float(likes.replace('万', '')) * 10000
                        
                        # 提取图片和视频 (获取链接但不下载)
                        image_urls, _ = self.extract_images(card, keyword, weibo_id)
                        video_urls, _ = self.extract_videos(card, keyword, weibo_id)
                        
                        # 组织数据
                        weibo_data = {
                            'keyword': keyword,
                            'weibo_id': weibo_id,
                            'user_name': user_name,
                            'user_link': user_link,
                            'content': content,
                            'publish_time': publish_time,
                            'forwards': likes ,
                            'comments': forwards,
                            'likes': comments,
                            'image_urls': '|'.join(image_urls),
                            'video_urls': '|'.join(video_urls),
                            'has_images': len(image_urls) > 0,
                            'has_videos': len(video_urls) > 0,
                            'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        results.append(weibo_data)
                    except Exception as e:
                        print(f"解析微博卡片时出错: {e}")
                
                # 随机延迟，避免频繁请求
                delay = self._get_random_delay()
                print(f"第 {page} 页爬取完成，休眠 {delay:.2f} 秒...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"爬取第 {page} 页时出错: {e}")
        
        return results
    
    def set_cookies(self, cookie_str):
        """
        设置Cookie，提高爬取效果
        
        参数:
        - cookie_str: Cookie字符串
        """
        if not cookie_str:
            return
        
        # 解析Cookie字符串为字典
        cookies = {}
        for item in cookie_str.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookies[key] = value
        
        self.cookies = cookies
        print("Cookie设置成功")
