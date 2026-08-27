---
title: "从这里开始"
slug: "start-here"
date: 2026-08-20T12:00:00+08:00
draft: false
tags:
  - 博客
  - Markdown
description: "一篇用于验证中文、代码和常见 Markdown 元素的示例文章。"
---

这是博客的示例文章。将现有 Markdown 放入 `content/posts/`，Hugo 就会在构建时自动发现并渲染它们。

> 页面采用温暖的纸张色背景、克制的蓝色链接和 720px 阅读列，适合长篇中文阅读。

## Markdown 内容

普通列表、引用、表格、图片与代码块都会使用统一的排版样式：

- 文章按照年份归档；
- 页面自动生成日期、字数和标签信息；
- 代码块支持语法高亮和横向滚动；
- 手机端会自动收窄页面并调整底部导航。

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, GitHub Pages")
}
```

| 项目 | 说明 |
| --- | --- |
| 文章目录 | `content/posts/` |
| 静态资源 | `static/` |
| 站点配置 | `hugo.yaml` |

完成配置后，可以删除这篇示例文章。
