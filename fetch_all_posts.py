#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
from datetime import datetime, timedelta
from fetch import WeiboSpider
import re

def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def save_results(results, filename_prefix="user_posts"):
    """保存结果到CSV文件"""
    if not results:
        print("没有数据需要保存")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/{filename_prefix}_{timestamp}.csv"
    
    try:
        import os
        import csv
        os.makedirs("results", exist_ok=True)
        
        # 读取可选的过滤配置（今天和昨天）。若无config或无键，则默认启用最近2个自然日过滤
        try:
            cfg = load_config()
        except Exception:
            cfg = {}
        enable_filter = cfg.get('enable_time_filter', True)
        recent_days = int(cfg.get('filter_recent_calendar_days', 2)) if enable_filter else 0

        def parse_weibo_time_for_results(time_str, now=None):
            if now is None:
                now = datetime.now()
            s = str(time_str).strip()
            if not s:
                return None
            # 英文格式: Thu Aug 07 16:59:47 +0800 2025
            try:
                dt_aware = datetime.strptime(s, '%a %b %d %H:%M:%S %z %Y')
                local_tz = datetime.now().astimezone().tzinfo
                dt_local = dt_aware.astimezone(local_tz)
                return dt_local.replace(tzinfo=None)
            except Exception:
                pass
            # 相对时间/中文格式（简化处理）
            if '昨天' in s:
                try:
                    t = s.replace('昨天', '').strip()
                    hhmm = datetime.strptime(t, '%H:%M')
                    return now.replace(hour=hhmm.hour, minute=hhmm.minute, second=0, microsecond=0) - timedelta(days=1)
                except Exception:
                    return now - timedelta(days=1)
            if '今天' in s:
                try:
                    t = s.replace('今天', '').strip()
                    hhmm = datetime.strptime(t, '%H:%M')
                    return now.replace(hour=hhmm.hour, minute=hhmm.minute, second=0, microsecond=0)
                except Exception:
                    return now
            if '分钟前' in s:
                try:
                    minutes = int(re.sub(r'\D', '', s))
                    return now - timedelta(minutes=minutes)
                except Exception:
                    return now
            if '小时前' in s:
                try:
                    hours = int(re.sub(r'\D', '', s))
                    return now - timedelta(hours=hours)
                except Exception:
                    return now
            # 形如 2024-05-23 12:34
            try:
                return datetime.strptime(s, '%Y-%m-%d %H:%M')
            except Exception:
                pass
            # 形如 05-23 12:34 （补年）
            try:
                return datetime.strptime(f"{now.year}-" + s, '%Y-%m-%d %H:%M')
            except Exception:
                pass
            return None

        def within_recent_days(dt_obj, now, days):
            if dt_obj is None:
                return False
            start_date = (now.date() - timedelta(days=days - 1))
            return start_date <= dt_obj.date() <= now.date()

        if enable_filter and recent_days > 0:
            now_dt = datetime.now()
            before_len = len(results)
            results = [r for r in results if within_recent_days(parse_weibo_time_for_results(r.get('publish_time', ''), now=now_dt), now_dt, recent_days)]
            print(f"时间过滤（最近{recent_days}个自然日）后保留 {len(results)}/{before_len} 条")

        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # 写入CSV表头
            writer.writerow(['keyword', 'weibo_id', 'content', 'publish_time', 'reposts_count', 'comments_count', 'attitudes_count', 'post_link'])
            
            # 写入数据行
            for item in results:
                # 构建微博链接
                post_link = f"https://weibo.com/detail/{item['weibo_id']}"
                
                # 清理内容中的换行和特殊字符
                content = item['content'].replace('\n', ' ').replace('\r', ' ').strip()
                
                # 使用用户名作为keyword，如果没有则使用用户ID
                keyword = item.get('user_name', f"user_{item['user_id']}")
                
                writer.writerow([
                    keyword,
                    item['weibo_id'],
                    content,
                    item['publish_time'],
                    item['reposts_count'],
                    item['comments_count'],
                    item['attitudes_count'],
                    post_link
                ])
        
        print(f"结果已保存到: {filename}")
        print(f"总共保存了 {len(results)} 条微博数据")
        
    except Exception as e:
        print(f"保存结果时出错: {e}")

def main():
    """主函数"""
    print("开始爬取指定用户的所有帖子...")
    
    # 指定要爬取的用户URL
    target_users = [
        "https://weibo.com/u/7051114584",
        "https://weibo.com/u/1669879400", 
        "https://weibo.com/u/5456865382",
        "https://weibo.com/u/5653796775"
    ]
    
    # 加载配置
    config = load_config()
    download_media = config.get('download_media', False)
    
    # 初始化爬虫
    spider = WeiboSpider()
    
    all_results = []
    
    for user_url in target_users:
        print(f"\n正在处理用户: {user_url}")
        
        try:
            # 爬取用户的第一页所有帖子
            results = spider.fetch_user_posts(
                user_url=user_url, 
                pages=1,  # 只爬取第一页
                download_media=download_media
            )
            
            if results:
                all_results.extend(results)
                print(f"用户 {user_url} 爬取完成，获得 {len(results)} 条微博")
            else:
                print(f"用户 {user_url} 未获取到微博数据")
            
            # 在处理下一个用户前添加延迟
            time.sleep(5)
            
        except Exception as e:
            print(f"处理用户 {user_url} 时出错: {e}")
            continue
    
    # 保存所有结果
    if all_results:
        save_results(all_results, "all_results")
        
        # 输出统计信息
        print(f"\n=== 爬取完成 ===")
        print(f"总共处理了 {len(target_users)} 个用户")
        print(f"总共获得 {len(all_results)} 条微博")
        
        # 按用户统计
        user_stats = {}
        for post in all_results:
            user_id = post.get('user_id', '未知')
            user_name = post.get('user_name', '未知')
            if user_id not in user_stats:
                user_stats[user_id] = {'name': user_name, 'count': 0}
            user_stats[user_id]['count'] += 1
        
        print("\n各用户微博数量统计:")
        for user_id, stats in user_stats.items():
            print(f"  {stats['name']} (ID: {user_id}): {stats['count']} 条")
    
    else:
        print("未获取到任何微博数据")

if __name__ == "__main__":
    main()