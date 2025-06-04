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

def image_to_base64(image_path, max_size=(400, 400)):
    """将图片转换为Base64编码"""
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 调整图片大小
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存到内存中
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            # 转换为Base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{image_base64}"
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")
        return None

def create_simple_gallery():
    """创建简化版图片画廊"""
    media_dir = 'media'
    results_dir = 'results'
    
    if not os.path.exists(media_dir):
        print("媒体目录不存在")
        return
        
    # 读取最新的汇总结果
    result_files = [f for f in os.listdir(results_dir) if f.startswith('all_results_') and f.endswith('.csv')]
    if not result_files:
        print("未找到结果文件")
        return
        
    latest_result = sorted(result_files)[-1]
    result_path = os.path.join(results_dir, latest_result)
    
    print(f"读取结果文件: {result_path}")
    df = pd.read_csv(result_path)
    
    # 创建HTML内容
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微博图片画廊 - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
            margin-bottom: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
        .keyword-section {{ 
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            overflow: hidden;
        }}
        .keyword-header {{ 
            background: #f8f9fa;
            padding: 1.5rem;
            border-bottom: 1px solid #e9ecef;
        }}
        .keyword-title {{ 
            font-size: 1.5rem;
            font-weight: 600;
            color: #495057;
            margin-bottom: 0.5rem;
        }}
        .keyword-stats {{ 
            color: #6c757d;
            font-size: 0.9rem;
        }}
        .image-grid {{ 
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            padding: 1.5rem;
        }}
        .image-card {{ 
            border-radius: 8px;
            overflow: hidden;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .image-card:hover {{ 
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        .image-container {{ 
            height: 250px;
            overflow: hidden;
            background: #f8f9fa;
        }}
        .image {{ 
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}
        .image-card:hover .image {{ transform: scale(1.05); }}
        .card-content {{ padding: 1rem; }}
        .image-filename {{ 
            font-size: 0.8rem;
            color: #6c757d;
            margin-bottom: 0.5rem;
            word-break: break-all;
        }}
        .image-info {{ 
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            color: #6c757d;
            margin-bottom: 1rem;
        }}
        .weibo-content {{ 
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .user-name {{ 
            font-weight: 600;
            color: #e6162d;
            margin-bottom: 0.5rem;
        }}
        .content-text {{ 
            margin-bottom: 0.75rem;
            line-height: 1.4;
        }}
        .stats {{ 
            display: flex;
            gap: 1rem;
            font-size: 0.85rem;
            color: #6c757d;
        }}
        .stat-item {{ 
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        .no-image {{ 
            background: #e9ecef;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6c757d;
            font-size: 0.9rem;
        }}
        .summary {{ 
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>微博图片画廊</h1>
            <p>生成时间: {timestamp}</p>
        </div>
    </div>
    
    <div class="container">
"""
    
    # 统计信息
    total_images = 0
    total_keywords = 0
    
    # 遍历每个关键词目录
    for keyword_dir in os.listdir(media_dir):
        keyword_path = os.path.join(media_dir, keyword_dir)
        if not os.path.isdir(keyword_path):
            continue
            
        print(f"处理关键词: {keyword_dir}")
        
        # 获取该关键词的微博数据
        keyword_data = df[df['keyword'] == keyword_dir]
        
        # 获取图片文件
        image_files = [f for f in os.listdir(keyword_path) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        if not image_files:
            continue
            
        total_keywords += 1
        total_images += len(image_files)
        
        # 添加关键词部分
        html_content += f"""
        <div class="keyword-section">
            <div class="keyword-header">
                <div class="keyword-title">{keyword_dir}</div>
                <div class="keyword-stats">
                    微博数量: {len(keyword_data)} | 图片数量: {len(image_files)} | 
                    分类: {keyword_data.iloc[0]['type'] if not keyword_data.empty and 'type' in keyword_data.columns else '未知'}
                </div>
            </div>
            <div class="image-grid">
"""
        
        # 处理前9张图片
        for i, image_file in enumerate(image_files[:9]):
            image_path = os.path.join(keyword_path, image_file)
            
            # 转换图片为Base64
            image_base64 = image_to_base64(image_path)
            
            # 提取微博ID
            weibo_id = None
            if 'image_' in image_file:
                try:
                    weibo_id = image_file.split('_')[1].split('?')[0]
                except:
                    pass
            
            # 查找对应的微博数据
            weibo_data = None
            if weibo_id and not keyword_data.empty:
                matching_weibo = keyword_data[keyword_data['weibo_id'].str.contains(weibo_id, na=False)]
                if not matching_weibo.empty:
                    row = matching_weibo.iloc[0]
                    weibo_data = {
                        'user_name': str(row['user_name']),
                        'content': str(row['content'])[:150] + '...' if len(str(row['content'])) > 150 else str(row['content']),
                        'likes': int(row['likes']) if pd.notna(row['likes']) else 0,
                        'comments': int(row['comments']) if pd.notna(row['comments']) else 0,
                        'forwards': int(row['forwards']) if pd.notna(row['forwards']) else 0
                    }
            
            # 获取文件大小
            file_size = os.path.getsize(image_path)
            size_mb = round(file_size / (1024 * 1024), 2)
            
            html_content += f"""
                <div class="image-card">
                    <div class="image-container">
"""
            
            if image_base64:
                html_content += f'<img src="{image_base64}" alt="{image_file}" class="image">'
            else:
                html_content += '<div class="no-image">图片加载失败</div>'
            
            html_content += f"""
                    </div>
                    <div class="card-content">
                        <div class="image-filename">{image_file}</div>
                        <div class="image-info">
                            <span>大小: {size_mb} MB</span>
                        </div>
"""
            
            if weibo_data:
                html_content += f"""
                        <div class="weibo-content">
                            <div class="user-name">@{weibo_data['user_name']}</div>
                            <div class="content-text">{weibo_data['content']}</div>
                            <div class="stats">
                                <div class="stat-item">👍 {weibo_data['likes']:,}</div>
                                <div class="stat-item">💬 {weibo_data['comments']:,}</div>
                                <div class="stat-item">🔄 {weibo_data['forwards']:,}</div>
                            </div>
                        </div>
"""
            
            html_content += """
                    </div>
                </div>
"""
        
        if len(image_files) > 9:
            html_content += f'<p style="grid-column: 1/-1; text-align: center; color: #6c757d;">还有 {len(image_files) - 9} 张图片...</p>'
        
        html_content += """
            </div>
        </div>
"""
    
    # 添加总结信息
    html_content += f"""
        <div class="summary">
            <h2>统计总览</h2>
            <p>共处理 <strong>{total_keywords}</strong> 个关键词，包含 <strong>{total_images}</strong> 张图片</p>
        </div>
    </div>
</body>
</html>
"""
    
    # 保存HTML文件
    html_file = f'simple_gallery_{timestamp}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"简化版图片画廊已保存到: {html_file}")
    return html_file

if __name__ == "__main__":
    create_simple_gallery() 