+++
date = '2025-05-30'
draft = false
title = 'kaniko 与 buildpacks, slugbuilder, slugrunner'
summary = ' '

+++



# kaniko

## 什么是 kaniko？

学习 kaniko 之前，先要了解什么是 docker daemon
docker daemon（docker 守护进程） 是 docker 的核心后台服务，在后台管理所有与容器相关的事情
比如：

1. 镜像管理：下载、存储、构建镜像（`docker pull`）
2. 容器生命周期：创建、启动、停止、删除容器（`docker run / stop / rm`）
3. 资源分配：给容器分配 cpu、内存等
4. 网络和存储：管理容器的网络连接和文件存储

举个例子，当我们运行 `docker build` 时，表面上是我们输入了 build 命令，实际上是 docker cli 把构建请求发送给 docker daemon，之后 daemon 读取 dockerfile，下载基础镜像，执行每一层指令，生成最终镜像，全程由 daemon 在后台完成

了解 docker daemon 后，再了解什么是 kaniko：

kaniko 是 Google 推出的容器工具，主要目的是在 **避免使用 docker daemon 的前提下，根据 dockerfile 构建 docker 镜像**，适用于在 容器内 / k8s 集群中构建镜像

- 一般来说，docker daemon 默认运行在宿主机上。如果想在 docker 容器中进行镜像的构建，就需要在容器内运行一个独立的 docker daemon，也就是 Docker-in-Docker(DinD)，使容器具备完整的构建能力
- 或者，可以将宿主机的 docker daemon 套接字挂载到容器内，容器直接调用宿主机的 daemon 构建镜像

## 为什么需要 kaniko

docker 构建镜像是 daemon-based 的，强依赖于宿主机上的 docker daemon 并且需要 **特权模式**，这对于强调 **隔离性和安全** 的云原生来说是不太能接受的，因此需要一种能够不使用 docker daemon 就可以构建容器镜像的方式，也就是 kaniko 存在的原因。

- 安全性：

  - 传统的 `docker build` 必须用到宿主机的资源，包括 root 权限或 docker 用户组权限、挂载 /var/run/docker.sock，如果出现漏洞或者恶意操作，宿主机就可能被入侵。

  - 而 kaniko 可以在非特权容器（无需 --privileged）中构建镜像，保证了安全问题

- 隔离性：
  - 传统的 docker 必须通过宿主机的 docker daemon 执行构建，存在权限相关问题
  - kaniko 完全在 用户空间 模拟 docker 构建流程，无需特权权限，彻底隔离了宿主机敏感资源

# buildpacks, slugbuilder, slugrunner

## 什么是 buildpacks？

buildpacks 是一种自动化构建工具，用于将应用程序源代码转化为可运行的容器镜像，然后上传到制品库中，无需手动编写 dockerfile。并且 buildpacks 可以将源代码构建为符合 OCI 规范的镜像。

## buildpacks 如何工作？

CNB(Cloud Native Buildpacks) 主要由 3 个组件组成：**Builder、Buildpack 和 Stack**

### Buildpack

本质是一个可执行单元的集合，负责监测代码类型并完成构建，比如：

- detect 脚本检查代码特征，比如发现 pom.xml 则判定为 Java 项目
- build 脚本负责安装依赖、编译代码，生成可运行的应用层
- 每个 buildpack 专注一种语言，多个 buildpack 可组合使用

### Builder

buildpacks 会通过 “检测”、“构建”、“输出” 完成一个构建逻辑，为了完成一个应用的构建，通常会使用到多个 buildpacks，那么 builder 就相当于一个 “构建工厂”，负责 **将应用源代码构建成应用镜像**，builder 中包含：

- 多个有序的 buildpack（比如先 Java 后 Node.js）
- 基础环境镜像
- Lifecycle（检测、构建、导出镜像）

### Stack

build image 为 Builders 提供基础环境（比如带 maven 的 Ubuntu 镜像），`run image` 在运行时为应用镜像提供基础环境，Stack 就是这两者的组合。

### 工作流程 belike

以 Django 项目为例：

1. 检测阶段（Detect）：

   Builder 中的每个 Buildpack 依次检查代码：

   - Python Buildpack 发现 requirement.txt，标记自己为 “适用”
   - Django Buildpack 进一步检测 manage.py 或 settings.py，确认 Django 框架存在
   - 其他 Buildpack 若未检测到特征，比如 Node.js 未检测到 package.json，则跳过 

2. 构建阶段（Build）
   依赖安装

   - 根据 requirement.txt 安装 python 依赖，缓存到独立层（避免重复下载）
   - 自动创建激活虚拟环境
     - 静态文件处理
   - 运行 python manage.py collectstatic 收集静态文件
     - 数据库迁移
   - 运行 python manage.py migrate 生成数据库迁移文件
     - 启动配置
   - 设置环境变量，生成启动命令

3. 导出镜像（Export）

   - Lifecycle 将所有层（依赖、静态文件、编译结果）与 run image 合并
   - 生成符合 OCI 规范的最终镜像
   - 镜像自动继承 run image 的安全补丁

## slugbuilder, slugrunner

### slugbuilder

- builder 的一种，slugbuilder 会在基础的 heroku runner 镜像上加层，最后组成一个完整的可运行的镜像。

- slugbuilder 是镜像构建阶段的基础环境，通过顺序执行多个 buildpack 将应用源代码构建成镜像层


## slugrunner

- slugrunner 是应用运行阶段的基础环境，用于承载构建阶段的产物，组成可以最终运行的容器镜像