+++
date = '2025-03-10'
draft = false
title = 'Linux 常用命令'
summary = ' '
+++

## 1.文件与目录操作

| 命令                       | 作用             | 使用场景                       |
| -------------------------- | ---------------- | ------------------------------ |
| `ls -lh`                   | 显示目录文件列表 | 查看文件大小、权限、修改时间等 |
| `cd`                       | 切换目录         | 进入代码目录、日志目录等       |
| `pwd`                      | 显示当前路径     | 确认当前工作目录               |
| `mkdir -p dir`             | 创建目录         | 创建不存在的目录（含父级）     |
| `rm -rf file`              | 删除文件/目录    | 清理临时文件，删除无用日志     |
| `cp -r src dest`           | 复制文件/目录    | 备份代码、配置文件等           |
| `mv src dest`              | 移动/重命名文件  | 重命名日志、移动文件到目标目录 |
| `find /path -name "*.log"` | 查找文件         | 定位日志文件、查找大文件       |
| `du -sh file`              | 查看文件大小     | 确定哪些文件占用空间过大       |
| `df -h`                    | 查看磁盘使用情况 | 确保服务器磁盘空间足够         |



## 2.进程管理

| 命令                    | 作用                  | 使用场景               |
| ----------------------- | --------------------- | ---------------------- |
| `ps aux`                | 查看所有进程          | 查找某个进程的 PID     |
| `top` / `htop`          | 实时查看 CPU/内存使用 | 排查服务器性能问题     |
| `kill -9 PID`           | 强制结束进程          | 终止卡死的程序         |
| `pkill -f process_name` | 根据名称杀进程        | 结束 Web 服务器进程    |
| `nohup command &`       | 后台运行进程          | 运行服务后保持终端关闭 |
| `jobs` / `fg` / `bg`    | 管理后台进程          | 让任务在后台执行       |



## 3.网络调试

| 命令                           | 作用           | 使用场景                 |
| ------------------------------ | -------------- | ------------------------ |
| `ifconfig` / `ip a`            | 查看 IP 地址   | 确认服务器 IP            |
| `ping google.com`              | 测试网络连通性 | 检查网络是否可用         |
| `curl -I http://example.com`   | 发送 HTTP 请求 | 检测 API 是否正常        |
| `wget url`                     | 下载文件       | 获取远程资源             |
| `netstat -tulnp` / `ss -tulnp` | 查看监听端口   | 确保服务正确运行         |
| `telnet IP PORT`               | 测试端口连通性 | 确认服务是否开放端口     |
| `scp file user@remote:/path`   | 远程传输文件   | 部署代码到远程服务器     |
| `rsync -avz src dest`          | 高效同步文件   | 备份数据，服务器同步代码 |



## 4.日志管理

| 命令                            | 作用         | 使用场景           |
| ------------------------------- | ------------ | ------------------ |
| `cat file.log`                  | 显示完整日志 | 查看小型日志文件   |
| `less file.log`                 | 分页查看     | 适用于大日志文件   |
| `tail -f file.log`              | 实时查看日志 | 监控应用运行状态   |
| `grep "error" file.log`         | 过滤关键字   | 查找日志错误信息   |
| `awk '{print $1}' file.log`     | 处理文本     | 提取指定字段       |
| `sed -i 's/old/new/g' file.log` | 替换文本     | 修改日志或配置文件 |

