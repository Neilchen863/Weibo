# 🕷️ 微博智能爬虫系统

一个功能强大的微博内容自动化采集和分析系统，支持关键词搜索、智能过滤、机器学习分析和自动化部署。

## ✨ 主要特性

### 🔍 **智能爬取**
- 🎯 基于关键词的精准搜索
- 📊 支持多页批量采集
- 🖼️ 自动下载图片和视频
- 🔄 智能重试和错误处理

### 🧠 **AI 分析**
- 🤖 机器学习内容质量评估
- 📈 热门话题自动识别
- 🎭 情感分析和分类
- 🏷️ 智能标签和聚类

### 🚀 **自动化部署**
- 🐳 完整的 Docker 容器化
- ⏰ 定时任务自动执行
- 📱 健康检查和监控
- 🔄 故障自动恢复

## 🚀 快速开始

### 一键部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-username/weibo-spider.git
cd weibo-spider

# 2. 配置环境变量
cp env.example .env
nano .env  # 填入你的微博Cookie

# 3. 一键部署
chmod +x deploy.sh
./deploy.sh
```

### 📱 获取微博Cookie

1. 打开浏览器，访问 [weibo.com](https://weibo.com)
2. 登录你的微博账号
3. 按 `F12` 打开开发者工具
4. 切换到 `Network` 标签页
5. 刷新页面
6. 找到任意请求，查看 `Request Headers`
7. 复制 `Cookie` 字段的完整值
8. 粘贴到 `.env` 文件中

## 🛠️ 服务管理

```bash
./deploy.sh start     # 启动服务
./deploy.sh stop      # 停止服务
./deploy.sh restart   # 重启服务
./deploy.sh logs      # 查看日志
./deploy.sh status    # 查看状态
```

## 📊 数据输出

- **results/** - 爬取结果CSV文件
- **media/** - 下载的图片和视频
- **logs/** - 系统日志
- **models/** - 机器学习模型

## ⚙️ 配置说明

在 `.env` 文件中配置：

```bash
# 微博Cookie（必填）
WEIBO_COOKIE=你的微博Cookie

# 爬虫配置
DEFAULT_PAGES=5                    # 每个关键词爬取页数
DOWNLOAD_MEDIA=true                # 是否下载图片视频
SCHEDULE_INTERVAL_HOURS=6          # 定时运行间隔（小时）
RUN_ONCE=false                     # 是否只运行一次

# 过滤配置
MIN_LIKES=1000                     # 最小点赞数
MIN_COMMENTS=50                    # 最小评论数
MIN_FORWARDS=20                    # 最小转发数
```

## ⚠️ 注意事项

- 🔒 保护个人Cookie信息，不要分享
- 📋 遵守网站服务条款和robots.txt
- ⏱️ 设置合理的爬取间隔
- 💾 定期备份重要数据

## 📄 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！ 