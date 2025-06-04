#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片目录索引生成器
为每个关键词的图片生成详细索引，包含图片信息和对应的微博数据
"""

import os
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import hashlib
import urllib.parse

def get_image_info(image_path):
    """获取图片的详细信息"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            format = img.format
            size = os.path.getsize(image_path)
            
        # 计算文件MD5哈希值
        with open(image_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
            
        return {
            'width': width,
            'height': height,
            'format': format,
            'size_bytes': size,
            'size_mb': round(size / (1024 * 1024), 2),
            'hash': file_hash,
            'created_time': datetime.fromtimestamp(os.path.getctime(image_path)).isoformat()
        }
    except Exception as e:
        return {'error': str(e)}

def create_image_index():
    """创建图片目录索引"""
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
    
    # 创建图片索引
    image_index = {}
    
    # 遍历每个关键词目录
    for keyword_dir in os.listdir(media_dir):
        keyword_path = os.path.join(media_dir, keyword_dir)
        if not os.path.isdir(keyword_path):
            continue
            
        print(f"处理关键词: {keyword_dir}")
        
        # 获取该关键词的微博数据
        keyword_data = df[df['keyword'] == keyword_dir]
        
        # 创建关键词索引
        keyword_index = {
            'keyword': keyword_dir,
            'total_images': 0,
            'total_size_mb': 0,
            'weibo_count': len(keyword_data),
            'images': []
        }
        
        # 遍历图片文件
        for image_file in os.listdir(keyword_path):
            if image_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                image_path = os.path.join(keyword_path, image_file)
                
                # 获取图片信息
                image_info = get_image_info(image_path)
                
                # 尝试从文件名提取微博ID
                weibo_id = None
                if 'image_' in image_file:
                    try:
                        weibo_id = image_file.split('_')[1].split('?')[0]
                    except:
                        pass
                
                # 查找对应的微博数据
                weibo_data = None
                if weibo_id:
                    matching_weibo = keyword_data[keyword_data['weibo_id'].str.contains(weibo_id, na=False)]
                    if not matching_weibo.empty:
                        row = matching_weibo.iloc[0]
                        weibo_data = {
                            'weibo_id': str(row['weibo_id']),
                            'content': str(row['content'])[:100] + '...' if len(str(row['content'])) > 100 else str(row['content']),
                            'user_name': str(row['user_name']),
                            'likes': int(row['likes']) if pd.notna(row['likes']) else 0,
                            'comments': int(row['comments']) if pd.notna(row['comments']) else 0,
                            'forwards': int(row['forwards']) if pd.notna(row['forwards']) else 0
                        }
                
                # 添加图片信息到索引
                image_record = {
                    'filename': image_file,
                    'relative_path': os.path.join('media', keyword_dir, image_file).replace('\\', '/'),
                    'weibo_id': weibo_id,
                    'weibo_data': weibo_data,
                    **image_info
                }
                
                keyword_index['images'].append(image_record)
                keyword_index['total_images'] += 1
                if 'size_mb' in image_info:
                    keyword_index['total_size_mb'] += image_info['size_mb']
        
        keyword_index['total_size_mb'] = round(keyword_index['total_size_mb'], 2)
        image_index[keyword_dir] = keyword_index
    
    # 保存索引文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    index_file = f'image_index_{timestamp}.json'
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(image_index, f, ensure_ascii=False, indent=2)
    
    print(f"图片索引已保存到: {index_file}")
    
    # 创建HTML预览文件
    create_html_preview(image_index, timestamp)
    
    return image_index

def create_html_preview(image_index, timestamp):
    """创建HTML预览文件"""
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图片索引预览</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .keyword-section {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; }}
        .keyword-header {{ background-color: #f5f5f5; padding: 10px; margin: -15px -15px 15px -15px; }}
        .image-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }}
        .image-card {{ border: 1px solid #ccc; padding: 10px; }}
        .image-preview {{ max-width: 100%; height: 200px; object-fit: cover; }}
        .image-info {{ margin-top: 10px; font-size: 12px; }}
        .weibo-content {{ background-color: #f9f9f9; padding: 8px; margin-top: 8px; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>图片索引预览 - {timestamp}</h1>
"""
    
    for keyword, data in image_index.items():
        html_content += f"""
    <div class="keyword-section">
        <div class="keyword-header">
            <h2>{keyword}</h2>
            <p>微博数量: {data['weibo_count']} | 图片数量: {data['total_images']} | 总大小: {data['total_size_mb']} MB</p>
        </div>
        <div class="image-grid">
"""
        
        for image in data['images'][:6]:  # 只显示前6张图片
            # URL编码图片路径
            encoded_path = urllib.parse.quote(image['relative_path'], safe='/:')
            html_content += f"""
            <div class="image-card">
                <img src="{encoded_path}" alt="{image['filename']}" class="image-preview">
                <div class="image-info">
                    <strong>{image['filename']}</strong><br>
                    尺寸: {image.get('width', 'N/A')} x {image.get('height', 'N/A')}<br>
                    大小: {image.get('size_mb', 'N/A')} MB
"""
            
            if image['weibo_data']:
                html_content += f"""
                    <div class="weibo-content">
                        <strong>@{image['weibo_data']['user_name']}</strong><br>
                        {image['weibo_data']['content']}<br>
                        👍 {image['weibo_data']['likes']} | 💬 {image['weibo_data']['comments']} | 🔄 {image['weibo_data']['forwards']}
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        if data['total_images'] > 6:
            html_content += f"<p>还有 {data['total_images'] - 6} 张图片...</p>"
        
        html_content += """
        </div>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    html_file = f'image_preview_{timestamp}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML预览文件已保存到: {html_file}")

if __name__ == "__main__":
    create_image_index() 