#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from fetch import WeiboSpider
from datetime import datetime

class CookieTester:
    def __init__(self):
        self.spider = WeiboSpider()
        
    def test_cookie(self, cookie_str):
        """测试cookie有效性"""
        print("🔍 开始测试Cookie有效性...")
        print(f"📝 Cookie: {cookie_str[:50]}..." if len(cookie_str) > 50 else f"📝 Cookie: {cookie_str}")
        
        # 设置cookie
        self.spider.set_cookies(cookie_str)
        
        # 测试多个URL
        test_urls = [
            ('主搜索页', 'https://s.weibo.com/weibo?q=测试'),
            ('热搜页面', 'https://s.weibo.com/top/summary'),
            ('微博首页', 'https://weibo.com'),
        ]
        
        results = {}
        
        for name, url in test_urls:
            try:
                print(f"\n🌐 测试 {name}: {url}")
                response = requests.get(
                    url, 
                    headers=self.spider.headers, 
                    cookies=self.spider.cookies, 
                    timeout=10,
                    allow_redirects=True
                )
                
                status = response.status_code
                content_length = len(response.text)
                has_cards = 'card-wrap' in response.text
                needs_login = '登录' in response.text or 'login' in response.text.lower()
                has_captcha = '验证码' in response.text or 'captcha' in response.text.lower()
                
                results[name] = {
                    'status': status,
                    'length': content_length,
                    'has_cards': has_cards,
                    'needs_login': needs_login,
                    'has_captcha': has_captcha,
                    'url': response.url
                }
                
                print(f"   ✅ 状态码: {status}")
                print(f"   📄 响应长度: {content_length}")
                print(f"   🏷️  微博卡片: {'✅' if has_cards else '❌'}")
                print(f"   🔐 需要登录: {'⚠️' if needs_login else '✅'}")
                print(f"   🤖 验证码: {'⚠️' if has_captcha else '✅'}")
                print(f"   🔗 最终URL: {response.url}")
                
            except Exception as e:
                print(f"   ❌ 请求失败: {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    def analyze_results(self, results):
        """分析测试结果并给出建议"""
        print("\n" + "="*60)
        print("📊 Cookie测试结果分析")
        print("="*60)
        
        all_good = True
        issues = []
        
        for name, result in results.items():
            if 'error' in result:
                all_good = False
                issues.append(f"❌ {name}: 请求失败 - {result['error']}")
            elif result.get('needs_login', False):
                all_good = False
                issues.append(f"🔐 {name}: 需要重新登录")
            elif result.get('has_captcha', False):
                all_good = False
                issues.append(f"🤖 {name}: 触发验证码")
            elif not result.get('has_cards', False) and '搜索' in name:
                all_good = False
                issues.append(f"📄 {name}: 无法获取微博内容")
        
        if all_good:
            print("✅ Cookie状态良好，可以正常使用")
        else:
            print("❌ Cookie存在问题:")
            for issue in issues:
                print(f"   {issue}")
            
            print("\n💡 解决建议:")
            print("1. 🔄 更新Cookie - 重新登录微博网页版获取新Cookie")
            print("2. 🌐 使用PC端Cookie - 确保使用桌面版微博的Cookie")
            print("3. ⏰ 检查Cookie时效 - 微博Cookie通常24小时内有效")
            print("4. 🛡️  避免频繁请求 - 降低请求频率避免触发反爬虫")
            print("5. 🔄 重启程序 - 清除可能的状态缓存")
        
        return all_good
    
    def get_fresh_cookie_guide(self):
        """提供获取新Cookie的指导"""
        print("\n" + "="*60)
        print("🍪 如何获取新的微博Cookie")
        print("="*60)
        print("1. 打开浏览器，访问: https://weibo.com")
        print("2. 登录你的微博账号")
        print("3. 按F12打开开发者工具")
        print("4. 切换到 Network (网络) 标签")
        print("5. 刷新页面或进行搜索")
        print("6. 找到任意一个对weibo.com的请求")
        print("7. 在Request Headers中找到Cookie")
        print("8. 复制完整的Cookie值")
        print("9. 更新config.json文件中的cookie字段")
        print("\n⚠️  注意事项:")
        print("- 使用桌面版网站的Cookie，不要用移动版")
        print("- Cookie包含敏感信息，请妥善保管")
        print("- Cookie通常24小时内有效，需要定期更新")

def main():
    # 加载当前配置
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        current_cookie = config.get('cookie', '')
    except Exception as e:
        print(f"❌ 无法加载配置文件: {e}")
        return
    
    if not current_cookie:
        print("❌ 配置文件中没有找到Cookie")
        return
    
    # 创建测试器
    tester = CookieTester()
    
    # 测试当前cookie
    results = tester.test_cookie(current_cookie)
    
    # 分析结果
    is_good = tester.analyze_results(results)
    
    if not is_good:
        tester.get_fresh_cookie_guide()
        
        # 询问是否要更新cookie
        print(f"\n🔧 如果你有新的Cookie，请输入:")
        print("（直接回车跳过）")
        new_cookie = input("新Cookie: ").strip()
        
        if new_cookie:
            # 测试新cookie
            print(f"\n🔍 测试新Cookie...")
            new_results = tester.test_cookie(new_cookie)
            is_new_good = tester.analyze_results(new_results)
            
            if is_new_good:
                # 更新配置文件
                config['cookie'] = new_cookie
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                print("✅ 新Cookie已保存到配置文件")
            else:
                print("❌ 新Cookie也有问题，请检查")

if __name__ == "__main__":
    main() 