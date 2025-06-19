#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版图片画廊生成器
使用Base64编码直接嵌入图片来避免路径问题
"""

import os
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import base64
import io
import hashlib
import requests

def get_image_hash(image_path):
    """获取图片文件的哈希值用于去重"""
    try:
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None

def image_to_base64(image_path, max_size=(400, 400)):
    """将图片转换为Base64编码"""
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 调整图片大小
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存到内存
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)
            
            # 转换为Base64
            image_data = buffer.getvalue()
            base64_string = base64.b64encode(image_data).decode('utf-8')
            
            return f"data:image/jpeg;base64,{base64_string}"
    except Exception as e:
        print(f"转换图片失败 {image_path}: {e}")
        return None

def create_simple_gallery():
    """创建简化版视频画廊"""
    try:
        # 查找最新的结果文件
        results_dir = "results"
        if not os.path.exists(results_dir):
            print("结果目录不存在")
            return None
        
        # 查找最新的汇总CSV文件
        csv_files = [f for f in os.listdir(results_dir) if f.endswith(".csv")]
        if not csv_files:
            print("未找到结果文件")
            return None
        
        # 选择最新的文件
        latest_csv = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(results_dir, x)))
        csv_path = os.path.join(results_dir, latest_csv)
        
        print(f"读取结果文件: {csv_path}")
        
        # 读取CSV数据
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_path, encoding='utf-8')
        
        if df.empty:
            print("CSV文件为空")
            return None
            
        # 修复列名中的换行符
        df.columns = [col.strip().replace('\n', '') for col in df.columns]
        
        # 确保video_url列是字符串类型
        df['video_url'] = df['video_url'].fillna('').astype(str)
        df['video_cover'] = df['video_cover'].fillna('').astype(str)
        
        # 只保留有视频的微博（通过检查video_url字段）
        df = df[df['video_url'].str.strip() != ''].copy()
        if df.empty:
            print("没有找到包含视频的微博")
            return None
        
        # 全局视频预览图哈希集合，用于去重
        global_video_hashes = set()
        
        # 按关键词分组处理视频
        keyword_videos = {}
        total_videos = 0
        unique_videos = 0
        
        for keyword in df['keyword'].unique():
            print(f"处理关键词: {keyword}")
            keyword_data = df[df['keyword'] == keyword]
            keyword_videos[keyword] = []
            
            for _, row in keyword_data.iterrows():
                weibo_id = str(row.get('weibo_id', ''))
                content = str(row.get('content', ''))[:100] + "..." if len(str(row.get('content', ''))) > 100 else str(row.get('content', ''))
                video_url = str(row.get('video_url', ''))
                video_cover = str(row.get('video_cover', ''))
                
                if not video_url or video_url == 'nan':
                    video_url = f"https://weibo.com/detail/{weibo_id}"
                
                if not video_cover or video_cover == 'nan':
                    # 使用默认的视频封面图
                    video_cover = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+CiAgPHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiM0NDQ0NDQiLz4KICA8Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIzMCIgZmlsbD0iI2ZmZmZmZiIgZmlsbC1vcGFjaXR5PSIwLjgiLz4KICA8cG9seWdvbiBwb2ludHM9IjQwLDM1IDY1LDUwIDQwLDY1IiBmaWxsPSIjNDQ0NDQ0Ii8+Cjwvc3ZnPg=="
                else:
                    try:
                        # 下载视频预览图
                        response = requests.get(video_cover, timeout=10)
                        if response.status_code == 200:
                            # 转换预览图为Base64
                            base64_string = base64.b64encode(response.content).decode('utf-8')
                            video_cover = f"data:image/jpeg;base64,{base64_string}"
                    except Exception as e:
                        print(f"下载视频预览图失败 {weibo_id}: {e}")
                        # 使用默认的视频封面图
                        video_cover = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+CiAgPHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiM0NDQ0NDQiLz4KICA8Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSIzMCIgZmlsbD0iI2ZmZmZmZiIgZmlsbC1vcGFjaXR5PSIwLjgiLz4KICA8cG9seWdvbiBwb2ludHM9IjQwLDM1IDY1LDUwIDQwLDY1IiBmaWxsPSIjNDQ0NDQ0Ii8+Cjwvc3ZnPg=="
                
                # 生成唯一标识
                video_hash = hashlib.md5(f"{weibo_id}_{content}".encode()).hexdigest()
                total_videos += 1
                
                # 只处理唯一视频
                if video_hash not in global_video_hashes:
                    global_video_hashes.add(video_hash)
                    unique_videos += 1
                    
                    keyword_videos[keyword].append({
                        'base64': video_cover,
                        'content': content,
                        'weibo_id': weibo_id,
                        'video_url': video_url
                    })
                    print(f"处理视频成功: {weibo_id}")
        
        # 生成HTML
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"video_gallery_{now}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微博视频画廊 - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            text-align: center;
            padding: 40px 20px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .stats {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px auto;
            max-width: 600px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            text-align: center;
        }}
        
        .stat-item {{
            font-size: 1.1em;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        
        .keyword-section {{
            margin: 40px 0;
            padding: 0 30px;
        }}
        
        .keyword-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding: 15px 25px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border-radius: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .keyword-stats {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .video-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .video-card {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            cursor: pointer;
        }}
        
        .video-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }}
        
        .video-preview {{
            position: relative;
            width: 100%;
            height: 250px;
            overflow: hidden;
        }}
        
        .video-preview img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .play-button {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 60px;
            height: 60px;
            background: rgba(0, 0, 0, 0.7);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: background 0.3s ease;
        }}
        
        .play-button::after {{
            content: '';
            width: 0;
            height: 0;
            border-style: solid;
            border-width: 10px 0 10px 20px;
            border-color: transparent transparent transparent white;
            margin-left: 5px;
        }}
        
        .video-info {{
            padding: 15px;
        }}
        
        .video-content {{
            font-size: 0.9em;
            color: #666;
            line-height: 1.5;
            margin-bottom: 10px;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .video-grid {{
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
            }}
            
            .keyword-title {{
                font-size: 1.4em;
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 微博视频画廊</h1>
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-number">{len([k for k in keyword_videos.keys() if keyword_videos[k]])}</span>
                    关键词
                </div>
                <div class="stat-item">
                    <span class="stat-number">{unique_videos}</span>
                    唯一视频
                </div>
                <div class="stat-item">
                    <span class="stat-number">{total_videos - unique_videos}</span>
                    去重删除
                </div>
                <div class="stat-item">
                    <span class="stat-number">{((total_videos - unique_videos) / total_videos * 100) if total_videos > 0 else 0:.1f}%</span>
                    去重率
                </div>
            </div>
        </div>
        
        <div class="content">
"""
        
        # 添加每个关键词的视频
        for keyword, videos in keyword_videos.items():
            if not videos:  # 跳过没有视频的关键词
                continue
                
            html_content += f"""
            <div class="keyword-section">
                <div class="keyword-title">
                    <span>🎥 {keyword}</span>
                    <span class="keyword-stats">{len(videos)} 个视频</span>
                </div>
                
                <div class="video-grid">
"""
            
            for video_data in videos:
                html_content += f"""
                    <div class="video-card" onclick="window.open('{video_data['video_url']}', '_blank')">
                        <div class="video-preview">
                            <img src="{video_data['base64']}" alt="视频预览">
                            <div class="play-button"></div>
                        </div>
                        <div class="video-info">
                            <div class="video-content">{video_data['content']}</div>
                        </div>
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        # 添加底部
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>🎯 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>📊 已智能去重，仅显示唯一视频</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 保存HTML文件
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"视频画廊已保存到: {html_filename}")
        print(f"去重统计: 总计 {total_videos} 个视频，保留 {unique_videos} 个唯一视频，删除 {total_videos - unique_videos} 个重复视频")
        
        return html_filename
        
    except Exception as e:
        print(f"生成视频画廊时出错: {e}")
        return None

if __name__ == "__main__":
    create_simple_gallery() 