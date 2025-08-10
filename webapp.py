#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import glob
import time
import threading
import subprocess
from collections import deque
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, JSONResponse


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


# ============ 运行与日志全局状态 ============
_job_lock = threading.Lock()
_job_process: Optional[subprocess.Popen] = None
_job_reader_thread: Optional[threading.Thread] = None
_log_buffer = deque(maxlen=10000)


def _append_log(line: str) -> None:
    line = line.rstrip('\n')
    if not line:
        return
    _log_buffer.append(line)


def _clear_logs() -> None:
    _log_buffer.clear()


def _reader_worker(proc: subprocess.Popen) -> None:
    try:
        if proc.stdout is None:
            return
        for line in proc.stdout:
            try:
                _append_log(line)
            except Exception:
                pass
    finally:
        rc = proc.poll()
        _append_log(f"[任务结束] 退出码: {rc}")
        with _job_lock:
            global _job_process, _job_reader_thread
            _job_process = None
            _job_reader_thread = None


def _start_job() -> bool:
    """启动后台任务: 以子进程运行 main.py 并实时读取日志。"""
    global _job_process, _job_reader_thread
    with _job_lock:
        if _job_process is not None:
            return False
        _clear_logs()
        cmd = [sys.executable, '-u', 'main.py']
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=APP_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            _append_log(f"启动失败: {e}")
            return False
        _job_process = proc
        t = threading.Thread(target=_reader_worker, args=(proc,), daemon=True)
        _job_reader_thread = t
        t.start()
        _append_log('[任务启动] 已开始执行 main.py')
        return True


def _stop_job() -> bool:
    """停止后台任务: 终止子进程。"""
    global _job_process, _job_reader_thread
    with _job_lock:
        if _job_process is None:
            return False
        proc = _job_process
    try:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        _append_log('[任务停止] 已请求终止')
        return True
    except Exception as e:
        _append_log(f"停止失败: {e}")
        return False


def render_home(message: str = '', latest_file: Optional[str] = None) -> str:
    latest_link_html = ''
    if latest_file and os.path.exists(latest_file):
        filename = os.path.basename(latest_file)
        latest_link_html = f'<p>最近生成的CSV: <a href="/download/{filename}">{filename}</a></p>'
    message_html = f'<p class="msg">{message}</p>' if message else ''
    html = """
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>WeiboSpider Web</title>
  <style>
    :root {{ --bg: #0b1324; --card: #111a33; --muted: #8aa0c6; --text: #e6eefc; --primary: #3b82f6; --primary-2: #1d4ed8; --danger: #ef4444; --danger-2: #b91c1c; --border: rgba(255,255,255,.08); }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; background: linear-gradient(180deg, #0b1021 0%, #0e1430 100%); color: var(--text); padding: 24px; margin: 0; }}
    h2 {{ max-width: 980px; margin: 0 auto 14px; letter-spacing: .3px; }}
    .card {{ max-width: 980px; margin: 0 auto 16px; border: 1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.01)); border-radius: 12px; padding: 20px; box-shadow: 0 8px 30px rgba(0,0,0,.15); }}
    label {{ display:block; margin: 8px 0 6px; font-weight: 600; }}
    textarea {{ width: 100%; min-height: 120px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; font-size: 12px; background: #0c152d; border: 1px solid var(--border); color: var(--text); border-radius: 10px; padding: 10px 12px; outline: none; }}
    textarea:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59,130,246,.15); }}
    button {{ padding: 10px 16px; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; transition: transform .05s ease, background .2s; }}
    button:active {{ transform: translateY(1px); }}
    #runBtn {{ background: var(--primary); color: #fff; }}
    #runBtn:hover {{ background: var(--primary-2); }}
    button[type="button"] {{ background: var(--danger); color: #fff; }}
    button[type="button"]:hover {{ background: var(--danger-2); }}
    button:disabled {{ background: #334155; color: #cbd5e1; cursor: not-allowed; }}
    .muted {{ color: var(--muted); font-size: 13px; }}
    .msg {{ margin: 10px 0 0; color: #22c55e; font-size: 14px; }}
    details {{ border: 1px solid var(--border); border-radius: 10px; padding: 8px 12px; background: rgba(255,255,255,.03); }}
    details summary {{ cursor: pointer; }}
    #latestCsv {{ max-width: 980px; margin: 10px auto; }}
    pre#console {{ background:#0b1021;color:#a6e22e;padding:12px;border-radius:12px;height:360px;overflow:auto;white-space:pre-wrap;border:1px solid var(--border); max-width: 980px; margin: 0 auto; }}
  </style>
  <script>
    let logTimer = null;

    async function startJob(e) {
      e.preventDefault();
      const btn = document.getElementById('runBtn');
      btn.disabled = true; btn.innerText = '运行中…';
      const form = e.target;
      const formData = new FormData(form);
      await fetch('/run', { method: 'POST', body: formData });
      startPolling();
      return false;
    }

    async function stopJob() {
      await fetch('/stop', { method: 'POST' });
      stopPolling();
      startPolling();
    }

    function startPolling() {
      if (logTimer) return;
      logTimer = setInterval(fetchLogs, 1000);
    }
    function stopPolling() {
      if (logTimer) { clearInterval(logTimer); logTimer = null; }
    }
    async function fetchLogs() {
      const r = await fetch('/logs');
      const data = await r.json();
      const pre = document.getElementById('console');
      if (pre) {
        pre.textContent = data.logs || '';
        pre.scrollTop = pre.scrollHeight;
      }
      const link = document.getElementById('latestCsv');
      if (link && data.latest_csv) {
        link.innerHTML = `最近CSV: <a href=\"/download/${data.latest_csv_name}\">${data.latest_csv_name}</a>`;
      }
      const btn = document.getElementById('runBtn');
      if (btn) btn.disabled = data.running;
    }
    window.addEventListener('load', () => {
      startPolling();
      const form = document.getElementById('runForm');
      if (form) form.addEventListener('submit', startJob);
    });
  </script>
  </head>
  <body>
    <h2>WeiboSpider 网页版</h2>
    <div class=\"card\">
      <form id=\"runForm\" method=\"post\" action=\"/run\"> 
        <label for=\"cookie\"><strong>输入你的微博 Cookie</strong></label>
        <p class=\"muted\">建议直接粘贴浏览器里对 weibo.com 的整段 Cookie（格式：键=值; 键=值; ...）。推荐至少包含 <code>SUB</code>、<code>SUBP</code>、<code>WBPSESS</code>、<code>SCF</code> 等键。</p>
        <details style=\"margin:6px 0\"><summary class=\"muted\">如何获取 Cookie</summary>
          <ol class=\"muted\">
            <li>电脑浏览器登录 <code>weibo.com</code>。</li>
            <li>按 F12 打开开发者工具，切到 Network 标签，刷新页面。</li>
            <li>点任一请求（域名为 weibo.com），在 Request Headers 找到 <code>cookie</code>，复制整段值。</li>
            <li>或在 Application/存储 - Cookies - 选中 <code>weibo.com</code>，导出合并为 <code>key=value; key=value; ...</code>。</li>
          </ol>
        </details>
        <textarea id=\"cookie\" name=\"cookie\" required placeholder=\"SCF=...; SUB=...; SUBP=...; WBPSESS=...\"></textarea>
        <hr />
        <label for=\"keywords\"><strong>关键词与分类（可选）</strong></label>
        <p class=\"muted\">对应文件为 <code>keyword and classification.txt</code>（CSV，含两列：<code>关键词,分类</code>）。此处每行一条，格式：<code>关键词,分类</code>；若省略分类则默认 <code>other</code>。</p>
        <textarea id=\"keywords\" name=\"keywords\" placeholder=\"淬火年代,show\n路透,other\n演唱会,other\"></textarea>
        <label for=\"user_urls\"><strong>用户URL（可选）</strong></label>
        <p class=\"muted\">每行一个 weibo 用户主页 URL；如留空则使用项目根目录的 <code>user_urls.txt</code>。</p>
        <textarea id=\"user_urls\" name=\"user_urls\" placeholder=\"https://weibo.com/u/1669879400\nhttps://weibo.com/u/7051114584\"></textarea>
        <p class=\"muted\">提交后：写入 <code>config.json</code>（Cookie）与 <code>keyword and classification.txt</code>/<code>user_urls.txt</code>（如提供），执行爬虫，完成后在下方提供 CSV 下载链接。</p>
        <button id=\"runBtn\" type=\"submit\">运行</button>
        <button type=\"button\" onclick=\"stopJob()\">停止</button>
      </form>
      [[MESSAGE]]
      [[LATEST_LINK]]
    </div>
    <p class=\"muted\" id=\"latestCsv\" style=\"margin:10px 0\"></p>
    <p class=\"muted\" style=\"margin-top:10px\">关键词从 <code>keyword and classification.txt</code> 读取（两列：<code>关键词,分类</code>）；用户从 <code>user_urls.txt</code> 读取；结果保存在 <code>results/</code>。</p>
    <h3>运行日志</h3>
    <pre id=\"console\" style=\"background:#0b1021;color:#a6e22e;padding:12px;border-radius:8px;height:320px;overflow:auto;white-space:pre-wrap;\"></pre>
  </body>
</html>
"""
    return html.replace('[[MESSAGE]]', message_html).replace('[[LATEST_LINK]]', latest_link_html)


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

    # 2) 可选写入关键词分类与用户URL文件
    try:
        if keywords is not None and keywords.strip():
            # 写入到 "keyword and classification.txt"。允许单列或两列（关键词,分类）。
            classification_path = os.path.join(APP_DIR, 'keyword and classification.txt')
            raw_lines = [line.strip() for line in keywords.replace('\r\n', '\n').split('\n') if line.strip()]
            rows = []
            for line in raw_lines:
                if ',' in line:
                    kw, cls = line.split(',', 1)
                    rows.append((kw.strip(), (cls.strip() or 'other')))
                else:
                    rows.append((line.strip(), 'other'))
            with open(classification_path, 'w', encoding='utf-8') as f:
                f.write('关键词,分类\n')
                for kw, cls in rows:
                    f.write(f'{kw},{cls}\n')
        if user_urls is not None and user_urls.strip():
            with open(os.path.join(APP_DIR, 'user_urls.txt'), 'w', encoding='utf-8') as f:
                lines = [line.strip() for line in user_urls.replace('\r\n', '\n').split('\n') if line.strip()]
                f.write('\n'.join(lines) + '\n')
    except Exception as e:
        latest = find_latest_csv()
        return render_home(message=f"写入关键词/用户URL失败: {e}", latest_file=latest)

    # 3) 启动后台任务（子进程执行 main.py），立即返回页面
    started = _start_job()
    if not started:
        latest = find_latest_csv()
        return render_home(message="已有任务在运行，无法重复启动。", latest_file=latest)

    # 4) 寻找最新 CSV 并展示下载链接
    latest = find_latest_csv()
    if latest:
        return render_home(message='任务已启动，检测到最近的 CSV。', latest_file=latest)
    else:
        return render_home(message='任务已启动，请在下方查看实时日志，完成后会出现 CSV 下载链接。', latest_file=None)


@app.get('/download/{filename}', response_class=FileResponse)
def download(filename: str):
    ensure_dirs()
    target_path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(target_path):
        return PlainTextResponse('文件不存在', status_code=404)
    return FileResponse(target_path, media_type='text/csv', filename=filename)


@app.get('/logs', response_class=JSONResponse)
def logs():
    with _job_lock:
        running = _job_process is not None and (_job_process.poll() is None)
    text = "\n".join(_log_buffer)
    latest = find_latest_csv()
    return {
        'running': running,
        'logs': text,
        'latest_csv': bool(latest),
        'latest_csv_name': os.path.basename(latest) if latest else ''
    }


@app.post('/stop', response_class=PlainTextResponse)
def stop():
    ok = _stop_job()
    return 'stopped' if ok else 'no-running-job'


# 开发时可直接: uvicorn webapp:app --host 0.0.0.0 --port 8000
