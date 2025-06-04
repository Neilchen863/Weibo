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
    """创建简化版图片画廊"""
    try:
        # 查找最新的结果文件
        results_dir = "results"
        if not os.path.exists(results_dir):
            print("结果目录不存在")
            return None
        
        # 查找最新的汇总CSV文件
        csv_files = [f for f in os.listdir(results_dir) if f.startswith("all_results_") and f.endswith(".csv")]
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
        
        # 全局图片哈希集合，用于去重
        global_image_hashes = set()
        
        # 按关键词分组处理图片
        keyword_images = {}
        total_images = 0
        unique_images = 0
        
        for keyword in df['keyword'].unique():
            print(f"处理关键词: {keyword}")
            keyword_data = df[df['keyword'] == keyword]
            keyword_images[keyword] = []
            
            for _, row in keyword_data.iterrows():
                weibo_id = str(row.get('weibo_id', ''))
                content = str(row.get('content', ''))[:100] + "..." if len(str(row.get('content', ''))) > 100 else str(row.get('content', ''))
                
                # 查找对应的图片目录
                image_dir = f"media/{keyword}"
                if not os.path.exists(image_dir):
                    continue
                
                # 查找匹配的图片文件
                for image_file in os.listdir(image_dir):
                    if weibo_id in image_file:
                        image_path = os.path.join(image_dir, image_file)
                        
                        # 获取图片哈希
                        image_hash = get_image_hash(image_path)
                        if not image_hash:
                            continue
                        
                        total_images += 1
                        
                        # 只处理唯一图片（全局去重）
                        if image_hash not in global_image_hashes:
                            global_image_hashes.add(image_hash)
                            unique_images += 1
                            
                            # 转换为Base64
                            base64_data = image_to_base64(image_path)
                            if base64_data:
                                keyword_images[keyword].append({
                                    'base64': base64_data,
                                    'content': content,
                                    'weibo_id': weibo_id,
                                    'filename': image_file
                                })
            
            # 显示关键词统计（仅唯一图片）
            unique_count = len(keyword_images[keyword])
            if unique_count > 0:
                print(f"关键词 '{keyword}': {unique_count} 张唯一图片")
        
        # 生成HTML
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"simple_gallery_{now}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微博图片画廊 - {datetime.now().strftime("%Y-%m-%d")}</title>
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
        
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .image-card {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .image-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }}
        
        .image-card img {{
            width: 100%;
            height: 250px;
            object-fit: cover;
            cursor: pointer;
        }}
        
        .image-info {{
            padding: 15px;
        }}
        
        .image-content {{
            font-size: 0.9em;
            color: #666;
            line-height: 1.5;
            margin-bottom: 10px;
        }}
        
        .image-meta {{
            font-size: 0.8em;
            color: #999;
            display: flex;
            justify-content: space-between;
        }}
        
        /* 模态框样式 */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }}
        
        .modal-content {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            max-width: 90%;
            max-height: 90%;
        }}
        
        .modal img {{
            width: 100%;
            height: auto;
            border-radius: 10px;
        }}
        
        .close {{
            position: absolute;
            top: 20px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        
        .close:hover {{
            color: #fff;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .image-grid {{
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
            <h1>🎨 微博图片画廊</h1>
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-number">{len([k for k in keyword_images.keys() if keyword_images[k]])}</span>
                    关键词
                </div>
                <div class="stat-item">
                    <span class="stat-number">{unique_images}</span>
                    唯一图片
                </div>
                <div class="stat-item">
                    <span class="stat-number">{total_images - unique_images}</span>
                    去重删除
                </div>
                <div class="stat-item">
                    <span class="stat-number">{((total_images - unique_images) / total_images * 100) if total_images > 0 else 0:.1f}%</span>
                    去重率
                </div>
            </div>
        </div>
        
        <div class="content">
"""
        
        # 添加每个关键词的图片
        for keyword, images in keyword_images.items():
            if not images:  # 跳过没有唯一图片的关键词
                continue
                
            html_content += f"""
            <div class="keyword-section">
                <div class="keyword-title">
                    <span>📱 {keyword}</span>
                    <span class="keyword-stats">{len(images)} 张图片</span>
                </div>
                
                <div class="image-grid">
"""
            
            for img_data in images:
                html_content += f"""
                    <div class="image-card">
                        <img src="{img_data['base64']}" alt="微博图片" onclick="openModal(this.src)">
                        <div class="image-info">
                            <div class="image-content">{img_data['content']}</div>
                        </div>
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        # 添加底部和JavaScript
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>🎯 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>📊 已智能去重，仅显示唯一图片</p>
        </div>
    </div>
    
    <!-- 模态框 -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="close" onclick="closeModal()">&times;</span>
        <div class="modal-content">
            <img id="modalImage" src="" alt="放大图片">
        </div>
    </div>
    
    <script>
        function openModal(src) {{
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            modal.style.display = 'block';
            modalImg.src = src;
        }}
        
        function closeModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}
        
        // ESC键关闭模态框
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>
"""
        
        # 保存HTML文件
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"简化版图片画廊已保存到: {html_filename}")
        print(f"去重统计: 总计 {total_images} 张图片，保留 {unique_images} 张唯一图片，删除 {total_images - unique_images} 张重复图片")
        
        return html_filename
        
    except Exception as e:
        print(f"生成图片画廊时出错: {e}")
        return None

if __name__ == "__main__":
    create_simple_gallery() 