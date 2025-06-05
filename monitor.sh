#!/bin/bash

# 微博爬虫监控脚本
# 用于检查服务状态并在需要时自动重启

LOG_FILE="/var/log/weibo-spider-monitor.log"
PROJECT_DIR="$(dirname "$(readlink -f "$0")")"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查容器状态
check_container() {
    local container_name="weibo-spider"
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        return 0  # 容器正在运行
    else
        return 1  # 容器未运行
    fi
}

# 检查容器健康状态
check_health() {
    local container_name="weibo-spider"
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null)
    
    if [ "$health_status" = "healthy" ]; then
        return 0
    else
        return 1
    fi
}

# 重启服务
restart_service() {
    log "重启微博爬虫服务..."
    
    cd "$PROJECT_DIR"
    
    # 停止现有服务
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null
    
    # 等待一段时间
    sleep 10
    
    # 启动服务
    if docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null; then
        log "服务重启成功"
        return 0
    else
        log "服务重启失败"
        return 1
    fi
}

# 发送通知（可扩展为钉钉、邮件等）
send_notification() {
    local message="$1"
    log "通知: $message"
    
    # 这里可以添加实际的通知逻辑
    # 例如：发送邮件、钉钉机器人、Slack等
    # curl -X POST "https://your-notification-webhook" -d "message=$message"
}

# 主监控逻辑
main() {
    log "开始监控检查..."
    
    if ! check_container; then
        log "容器未运行，尝试重启..."
        send_notification "微博爬虫容器未运行，正在重启..."
        
        if restart_service; then
            send_notification "微博爬虫服务重启成功"
        else
            send_notification "微博爬虫服务重启失败，需要人工干预"
        fi
    else
        # 容器在运行，检查健康状态
        if ! check_health; then
            log "容器运行但健康检查失败，尝试重启..."
            send_notification "微博爬虫容器健康检查失败，正在重启..."
            
            if restart_service; then
                send_notification "微博爬虫服务重启成功"
            else
                send_notification "微博爬虫服务重启失败，需要人工干预"
            fi
        else
            log "服务运行正常"
        fi
    fi
    
    # 检查磁盘空间
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        log "警告: 磁盘使用率过高 ($disk_usage%)"
        send_notification "微博爬虫服务器磁盘使用率过高: $disk_usage%"
    fi
    
    # 检查内存使用
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$memory_usage" -gt 90 ]; then
        log "警告: 内存使用率过高 ($memory_usage%)"
        send_notification "微博爬虫服务器内存使用率过高: $memory_usage%"
    fi
}

# 执行监控
main 