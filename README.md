# Minimal Hugo Blog

一个仿照 [wklken.me](https://wklken.me/) 阅读体验实现的极简 Hugo 博客：温暖的纸张色、固定底部导航、720px 正文列、按年份归档和深色代码块。

项目不依赖第三方 Hugo 主题，页面布局和样式都在仓库内，适合直接部署到 GitHub Pages。

## 目录

```text
.
├── content/
│   ├── posts/              # 把 Markdown 文章放在这里，可递归扫描子目录
│   └── about.md            # 关于页面
├── layouts/                # Hugo 页面模板
├── assets/css/main.css     # 全站样式
├── static/                 # 图片等静态文件
├── scripts/import_md.py    # 批量导入已有 Markdown
├── .github/workflows/      # GitHub Pages 自动部署
└── hugo.yaml               # 站点配置
```

## 1. 修改个人信息

编辑 `hugo.yaml`：

- 把 `YOUR-USERNAME` 换成 GitHub 用户名；
- 把 `MY THINKING` 换成博客标题；
- 修改 `params.author`、`params.tagline` 和 `params.github`；
- 如果不需要 Tags，可从 `menu.main` 中删除对应条目。

## 2. 放入 Markdown

最直接的方式是把文章复制到 `content/posts/`。Hugo 会递归读取其中所有 `.md` 文件。

推荐每篇文章包含 Front Matter：

```markdown
---
title: "文章标题"
slug: "my-post"
date: 2026-08-20T12:00:00+08:00
draft: false
tags: [Hugo, GitHub Pages]
description: "可选的文章摘要"
---

正文从这里开始。
```

如果现有文件没有 Front Matter，可以运行导入工具：

```bash
python3 scripts/import_md.py /绝对路径/你的文章目录
```

工具会递归复制 Markdown 到 `content/posts/imported/`，并根据已有 YAML、首个一级标题、文件名和修改时间补齐标题与日期。已有目标文件默认不会覆盖；需要覆盖时添加 `--force`。

图片建议放入 `static/images/`，在 Markdown 中使用 `/images/example.png`。如果博客发布在项目子路径，优先使用 Hugo shortcode 或相对路径。

## 3. 本地预览

安装 [Hugo Extended](https://gohugo.io/installation/) 0.165.0 或兼容版本：

```bash
hugo server -D
```

访问 `http://localhost:1313/`。正式构建：

```bash
hugo --gc --minify
```

生成结果位于 `public/`，该目录已加入 `.gitignore`。

## 4. 部署到 GitHub Pages

1. 在 GitHub 新建 `<你的用户名>.github.io` 仓库。
2. 将当前目录提交并推送到 `main` 分支。
3. 打开仓库 **Settings → Pages**，将 Source 设为 **GitHub Actions**。
4. 推送后，`.github/workflows/pages.yml` 会构建并发布站点。

工作流会使用 GitHub Pages 返回的实际地址覆盖 `baseURL`，因此同时支持用户站点和普通项目站点。

```bash
git init
git add .
git commit -m "Create minimal Hugo blog"
git branch -M main
git remote add origin git@github.com:YOUR-USERNAME/YOUR-USERNAME.github.io.git
git push -u origin main
```

## 常用操作

新建文章：

```bash
hugo new posts/my-new-post.md
```

预览草稿：

```bash
hugo server -D
```

删除示例文章：

```bash
rm content/posts/2026-08-20-start-here.md
```

发布前请检查 `draft: false`。
