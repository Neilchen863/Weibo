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
        self.seen_weibos = set()
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
    
    def download_media(self, url, media_type, keyword, weibo_id):
        """
        下载媒体文件（图片或视频）
        
        参数:
        - url: 媒体文件URL
        - media_type: 媒体类型 ('image' 或 'video')
        - keyword: 搜索关键词
        - weibo_id: 微博ID
        
        返回:
        - 本地文件路径
        """
        try:
            # 创建关键词专用目录
            keyword_dir = os.path.join(self.media_dir, keyword)
            os.makedirs(keyword_dir, exist_ok=True)
            
            # 获取文件扩展名
            file_ext = url.split('.')[-1].split('?')[0]
            if file_ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov']:
                file_ext = 'jpg'  # 默认为jpg
            
            # 生成文件名
            timestamp = int(time.time())
            filename = f"{media_type}_{weibo_id}_{timestamp}.{file_ext}"
            file_path = os.path.join(keyword_dir, filename)
            
            # 下载文件
            headers = self.headers.copy()
            headers['Referer'] = 'https://weibo.com/'
            
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"下载成功: {filename}")
            return file_path
            
        except Exception as e:
            print(f"下载失败 {url}: {e}")
            return ""
    
    def extract_images(self, card, keyword, weibo_id):
        """
        提取微博图片链接并可选下载
        
        参数:
        - card: 微博卡片元素
        - keyword: 搜索关键词
        - weibo_id: 微博ID
        
        返回:
        - (image_urls, local_paths) 元组
        """
        # 图片容器通常在这些位置
        image_nodes = card.xpath('.//div[contains(@class, "media-pic")]//img/@src') or \
                     card.xpath('.//div[@node-type="feed_list_media_prev"]//img/@src') or \
                     card.xpath('.//img[contains(@class, "pic")]/@src')
        
        # 清理URL地址
        image_urls = []
        local_paths = []
        
        for url in image_nodes:
            if url.startswith('//'):
                url = 'https:' + url
            
            # 将thumbnail链接转换为原图链接
            if '/thumb150/' in url:
                url = url.replace('/thumb150/', '/large/')
            elif '/bmiddle/' in url:
                url = url.replace('/bmiddle/', '/large/')
            
            image_urls.append(url)
            
            # 如果启用了媒体下载，则下载图片
            if self.download_media_enabled:
                local_path = self.download_media(url, 'image', keyword, weibo_id)
                if local_path:
                    local_paths.append(local_path)
                time.sleep(0.5)  # 短暂延迟，避免请求过快
        
        return image_urls, local_paths
    
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
        - download_media: 是否下载媒体文件
        
        返回:
        - 搜索结果列表
        """
        results = []
        self.download_media_enabled = download_media  # 根据参数设置下载状态
        
        end_page = start_page + pages - 1
        print(f"准备搜索关键词: {keyword}, 计划爬取 {start_page} 到 {end_page} 页")
        if download_media:
            print("已启用媒体下载功能")
        
        for page in tqdm(range(start_page, end_page + 1), desc="爬取进度"):
            try:
                # 构建搜索URL
                search_url = f"{self.base_url}?q={keyword}&xsort=hot&page={page}"
                
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
                        
                        # 提取微博ID和构建链接
                        weibo_id_raw = card.xpath('.//div[@class="from"]/a[1]/@href')
                        weibo_id = weibo_id_raw[0].split('/')[-1] if weibo_id_raw else "未知ID"

                        # 构建微博链接
                        if weibo_id_raw:
                            # 修复URL格式，确保不重复
                            href = weibo_id_raw[0]
                            # Debug: 打印href格式
                            # print(f"DEBUG href: {href}")
                            
                            if href.startswith('http'):
                                post_link = href
                            elif href.startswith('//weibo.com/'):
                                post_link = f"https:{href}"
                            elif href.startswith('/'):
                                post_link = f"https://weibo.com{href}"
                            else:
                                post_link = f"https://weibo.com/{href}"
                        else:
                            post_link = ""

                        if weibo_id in self.seen_weibos:
                            continue
                        self.seen_weibos.add(weibo_id)
                        
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
                        
                        likes = card.xpath('.//div[@class="card-act"]/ul/li[4]/a/em/text()') or \
                              card.xpath('.//div[@class="card-act"]/ul/li[1]//text()') or \
                              card.xpath('.//span[contains(text(), "转发")]/../text()') or \
                              card.xpath('.//a[contains(@href, "repost")]//text()') or \
                              card.xpath('.//li[contains(., "转发")]//text()')
                        likes = ''.join(likes).strip().replace('转发', '').replace(' ', '') if isinstance(likes, list) else (likes or '0')
                        if likes == '':
                            likes = '0'
                        if '万' in likes:
                            likes = float(likes.replace('万', '')) * 10000
                        
                        # 提取图片和视频（根据设置决定是否下载）
                        image_urls, image_paths = self.extract_images(card, keyword, weibo_id)
                        video_urls, video_paths = self.extract_videos(card, keyword, weibo_id)
                        
                        # 组织数据
                        weibo_data = {
                            'keyword': keyword,
                            'weibo_id': weibo_id,
                            'user_name': user_name,
                            'user_link': user_link,
                            'post_link': post_link,
                            'content': content,
                            'publish_time': publish_time,
                            'forwards': forwards,
                            'comments': comments,
                            'likes': likes,
                            'image_urls': '|'.join(image_urls),
                            'video_urls': '|'.join(video_urls),
                            'image_paths': '|'.join(image_paths),
                            'video_paths': '|'.join(video_paths),
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
