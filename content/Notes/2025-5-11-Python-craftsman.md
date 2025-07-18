+++
date = '2025-05-11'
draft = false
title = '《Python-craftsman》Reading notes'
summary = ' '
+++





## 前言

结束了暑期实习的面试后，非常幸运的，我加入了一个充满活力、技术氛围浓厚的技术团队。在入职 landing 四天里，我体会到了组里对实习生的热情关怀，同时也结交了一位非常优秀，兴趣相投的 mentor。

在这四天里，通过组里的大小会议和上班时的学习过渡，我慢慢了解了组里具体负责的业务和如何用 python 进行后端开发。

这本书的作者是我实习组里的 leader，在入职前就了解到他有出版过 python 相关的书籍，也借此机会来拜读一下。这篇 blog 应该是记录读这本书的过程和一些想法和收获吧，可能也会写一些实习期间的感触 ~



## Chapter 1：变量与注释

1. 什么是好的变量与注释？

变量和注释是代码里最接近自然语言的东西，最容易被人的大脑消化和理解，正因如此，如果程序员在编写变量和注释时含糊不清，阅读代码的人很难搞清楚代码的真实意图。比如下面两行代码，明显是后者更通俗易懂：

```python
# 去掉 s 两边的空格，再处理
value = process(s.trip())
```

```python
# 用户输入可能会有空格，使用 strip() 去掉空格
username = extract_username(input_string.strip())
```

2. 变量命名规则

   - 遵循 `PEP 8` 原则：这是 python 官方指定的编码风格指南，里面有许多详细的风格建议，比如应该用 4 个空格缩进，每行不超过 79 个字符等等。当然也包含变量的命名规范：
     - 对于普通变量，使用蛇形命名法，比如 `max_value`
     - 对于常量，采用全大写字母，并使用下划线连接，比如 `MAX_VALUE`
     - 如果变量标记为 “仅内部使用”，为其增加下划线前缀，比如 `_local_var`
     - 当名字与 python 关键字冲突时，在变量末尾追加下划线，比如 `class_`
   - 描述性要强：在可接受的长度范围内，变量名所指向的内容描述得越精确越好，比如上面提到的代码 `username = extract_username(input_string.strip())`
   - 要尽量短：注意，这一点和第二点并不冲突。在日常编码中，我们要在保证变量描述性的同时，还要确保变量名尽可能短。否则，在代码中可能会充斥着无比冗长的变量名，这给人带来的阅读体验也是非常糟糕的

3. 如何编写合格的注释内容

   - python 里的注释主要分为两种，一种是最常见的代码内注释，通过在行首输入 # 号来表示；另一种则是文档（docstring）类型注释（也可称为接口注释）

   - 需要弄清楚接口注释的受众，接口文档主要是给函数的使用者看的，它的存在价值在于让调用者不用逐行阅读函数代码，也能通过文档快速了解如何使用这个函数，以及使用时的注意事项，比如下面两段代码：

     ```python
     def resize_image(image, size):
         """将图⽚缩放到指定尺⼨，并返回新的图⽚。
         该函数将使⽤ Pilot 模块读取⽂件对象，然后调⽤ .resize() ⽅法将其缩放到指定尺⼨。
         但由于 Pilot 模块⾃⾝限制，这个函数不能很好地处理过⼤的⽂件，当⽂件⼤⼩超过 5MB 时，
         resize() ⽅法的性能就会因为内存分配问题急剧下降，详⻅ Pilot 模块的Issue #007。因此，
         对于超过 5MB 的图⽚⽂件，请使⽤ resize_big_image() 替代，后者基于 Pillow 模块开发，
         很好地解决了内存分配问题，确保性能更好了。
         :param image: 图⽚⽂件对象
         :param size: 包含宽⾼的元组：（width, height）
         :return: 新图⽚对象
         """
     ```

     ```python
     def resize_image(image, size):
         """将图⽚缩放到指定尺⼨，并返回新的图⽚。
         注意：当⽂件超过 5MB 时，请使⽤ resize_big_image()
         :param image: 图⽚⽂件对象
         :param size: 包含宽⾼的元组：（width, height）
         :return: 新图⽚对象
     	"""
     ```

4. 保持变量的一致性
   - 使用变量时，需要保证它在两个方面的一致性：**名字一致性** 与 **类型一致性**
     - 名字一致性：同一个项目中，对一类事物的称呼不要变来变去。比如项目中的 “用户头像” 命名为 `user_avatar_url` ，其他地方就别改成 `user_profile_url` ，否则会让读代码的人犯迷糊，这两个到底是不是一个东西？
     - 类型一致性：对于同一个变量，不要重复指向不同类型的值。我个人在做开发者中心沙箱相关优化时，commit 代码后 mypy 工具就报错：`error: Incompatible types in assignment` ，这是因为我在代码中对同一个变量反复赋不同类型的值。这样做会导致变量的辨识度降低，还很容易引入 bug

