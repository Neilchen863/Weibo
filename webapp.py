#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import glob
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, PlainTextResponse


APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, 'config.json')
RESULTS_DIR = os.path.join(APP_DIR, 'results')


def ensure_dirs() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)


def update_cookie_in_config(cookie: str) -> None:
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            config = {}
    config['cookie'] = cookie.strip()
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def find_latest_csv() -> Optional[str]:
    ensure_dirs()
    csv_files = sorted(glob.glob(os.path.join(RESULTS_DIR, 'all_results_*.csv')), key=os.path.getmtime, reverse=True)
    return csv_files[0] if csv_files else None


def render_home(message: str = '', latest_file: Optional[str] = None) -> str:
    latest_link_html = ''
    if latest_file and os.path.exists(latest_file):
        filename = os.path.basename(latest_file)
        latest_link_html = f'<p>最近生成的CSV: <a href="/download/{filename}">{filename}</a></p>'
    return f"""
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>WeiboSpider Web</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; padding: 24px; max-width: 860px; margin: 0 auto; }}
    .card {{ border: 1px solid #eee; border-radius: 8px; padding: 20px; box-shadow: 0 1px 2px rgba(0,0,0,.05); }}
    textarea {{ width: 100%; min-height: 120px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; font-size: 12px; }}
    button {{ background: #2563eb; color: #fff; padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; }}
    button:disabled {{ background: #94a3b8; }}
    .muted {{ color: #64748b; font-size: 13px; }}
    .msg {{ margin: 12px 0; color: #16a34a; }}
  </style>
  <script>
    function onSubmitForm() {{
      const btn = document.getElementById('runBtn');
      btn.disabled = true; btn.innerText = '运行中，请稍候…';
      return true;
    }}
  </script>
  </head>
  <body>
    <h2>WeiboSpider 网页版</h2>
    <div class=\"card\">
      <form method=\"post\" action=\"/run\" onsubmit=\"return onSubmitForm()\">
        <label for=\"cookie\"><strong>输入你的微博 Cookie</strong></label>
        <p class=\"muted\">建议直接粘贴浏览器里对 weibo.com 的整段 Cookie（以键=值; 键=值; ... 形式）。</p>
        <textarea id=\"cookie\" name=\"cookie\" required placeholder=\"SCF=...; SUB=...; SUBP=...; WBPSESS=...\"></textarea>
        <hr />
        <label for=\"keywords\"><strong>关键词（可选）</strong></label>
        <p class=\"muted\">每行一个关键词；如留空则使用项目根目录的 <code>keywords.txt</code>。</p>
        <textarea id=\"keywords\" name=\"keywords\" placeholder=\"演唱会\n粉丝见面会\n新歌\"></textarea>
        <label for=\"user_urls\"><strong>用户URL（可选）</strong></label>
        <p class=\"muted\">每行一个 weibo 用户主页 URL；如留空则使用项目根目录的 <code>user_urls.txt</code>。</p>
        <textarea id=\"user_urls\" name=\"user_urls\" placeholder=\"https://weibo.com/u/1669879400\nhttps://weibo.com/u/7051114584\"></textarea>
        <p class=\"muted\">本页面会将 Cookie 写入项目的 config.json，可选地写入关键词与用户URL文件，然后执行现有爬虫流程，完成后在下方提供 CSV 下载链接。</p>
        <button id=\"runBtn\" type=\"submit\">运行</button>
      </form>
      {('<p class="msg">' + message + '</p>') if message else ''}
      {latest_link_html}
    </div>
    <p class=\"muted\" style=\"margin-top:16px\">关键词与用户由项目根目录下的 <code>keywords.txt</code> 与 <code>user_urls.txt</code> 提供。结果保存在 <code>results/</code>。</p>
  </body>
</html>
"""


app = FastAPI(title="WeiboSpider Web")


@app.get('/', response_class=HTMLResponse)
def home() -> str:
    ensure_dirs()
    latest = find_latest_csv()
    return render_home(message='', latest_file=latest)


@app.get('/health', response_class=PlainTextResponse)
def health() -> str:
    return 'ok'


@app.post('/run', response_class=HTMLResponse)
def run(cookie: str = Form(...), keywords: Optional[str] = Form(None), user_urls: Optional[str] = Form(None)):
    ensure_dirs()
    # 1) 更新 cookie
    update_cookie_in_config(cookie)

    # 2) 可选写入 keywords 与 user_urls 文件
    try:
        if keywords is not None and keywords.strip():
            with open(os.path.join(APP_DIR, 'keywords.txt'), 'w', encoding='utf-8') as f:
                # 规范化换行并去掉空白行
                lines = [line.strip() for line in keywords.replace('\r\n', '\n').split('\n') if line.strip()]
                f.write('\n'.join(lines) + '\n')
        if user_urls is not None and user_urls.strip():
            with open(os.path.join(APP_DIR, 'user_urls.txt'), 'w', encoding='utf-8') as f:
                lines = [line.strip() for line in user_urls.replace('\r\n', '\n').split('\n') if line.strip()]
                f.write('\n'.join(lines) + '\n')
    except Exception as e:
        latest = find_latest_csv()
        return render_home(message=f"写入关键词/用户URL失败: {e}", latest_file=latest)

    # 3) 运行现有主流程
    try:
        from main import main as cli_main
        cli_main()
    except Exception as e:
        # 将异常展示给用户
        latest = find_latest_csv()
        return render_home(message=f"运行失败: {e}", latest_file=latest)

    # 4) 寻找最新 CSV 并展示下载链接
    latest = find_latest_csv()
    if latest:
        return render_home(message='运行完成！请点击下载最新 CSV。', latest_file=latest)
    else:
        return render_home(message='运行完成，但未找到 CSV 文件。请检查日志。', latest_file=None)


@app.get('/download/{filename}', response_class=FileResponse)
def download(filename: str):
    ensure_dirs()
    target_path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(target_path):
        return PlainTextResponse('文件不存在', status_code=404)
    return FileResponse(target_path, media_type='text/csv', filename=filename)


# 开发时可直接: uvicorn webapp:app --host 0.0.0.0 --port 8000
