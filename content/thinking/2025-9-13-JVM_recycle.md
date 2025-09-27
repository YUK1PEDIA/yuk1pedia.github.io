+++
date = '2025-09-13'
draft = false
title = '浅谈 JVM 垃圾回收机制'
summary = ' '
+++

## 垃圾回收的概念从何而来

垃圾回收（Garbage Collection, GC），顾名思义就是释放垃圾占用的空间，避免爆内存。具体来说，垃圾回收需要对 **堆内存** 中已经死亡或者长时间未使用的对象进行清除回收。

Java 语言问世之前，程序员大多数都是在写 C/C++ 程序。我们知道，C++ 这种没有 GC 机制的语言，创建对象时需要不断地开辟内存空间，不用该对象的时候又需要 **手动** 的去释放空间，既要写构造函数，又要写析构函数。比如下面使用 C++ 编写的 Person 类：

```c++
class Person {
private:
    std::string name;
    int age;

public:
    // 构造函数
    Person(const std::string& personName, int personAge) : name(personName), age(personAge) {}

    // 析构函数
    ~Person() {}

    void introduce() {
        std::cout << "Hello，my name is " << name << "， and I'm " << age << " years old now" << std::endl;
    }
};
```

在日常写代码的过程中，我们偏向于创建对象、调用对象方法来完成一个个的任务。但每次创建对象后如果都需要手动释放内存空间，会在代码段中引入大量的析构函数，既带来了不太丝滑的编程体验，也增加了阅读代码的工作量。

那么我们能不能专门写一段程序来实现析构函数的功能，每次创建对象、释放内存空间的时候复用这段代码？

在 1960 年，基于 MIT 的 Lisp 首先提出了 **垃圾回收** 的概念，用于处理 C/C++ 语言不停析构的操作。

到 1995 年 Java 问世，把垃圾回收的机制发扬光大。

## JVM & 垃圾判断算法

Java 虚拟机（Java Virtual Machine, JVM）是一种能够执行 Java 字节码的虚拟机。Java “一次编写，处处运行” 的特性离不开 JVM。

具体来说，Java 代码（.java 文件）编译后生成 **字节码**（.class 文件），JVM 负责将字节码动态翻译成 **目标平台的机器码**，从而实现在不同操作系统上运行同一份字节码文件。

同时，JVM 也承担着管理内存 —— **垃圾回收** 的重任。

既然 JVM 要做垃圾回收，就要搞清楚堆内存中什么是垃圾，通常会有两种算法来确定一个对象是否为垃圾：**引用计数算法** 和 **可达性分析算法**。

### 引用计数算法

该算法的原理比较简单：通过在对象头中分配一个空间来保存该对象被引用的次数，如果该对象被其他对象引用，引用计数 +1，如果删除对该对象的引用，引用计数 -1。

**当该对象的引用计数为 0，那么该对象就会被回收。**

这个算法实现简单，效率高，但目前主流的虚拟机中并没有选择该算法来管理内存，主要是因为它很难解决 **循环引用** 问题：

```java
public class ReferenceCountingGc {
    Object instance = null;
    public static void main(String[] args) {
        ReferenceCountingGc objA = new ReferenceCountingGc();
        ReferenceCountingGc objB = new ReferenceCountingGc();
        objA.instance = objB;
        objB.instance = objA;
        objA = null;
        objB = null;
    }
}
```

如上面代码所示，`objA` 和 `objB` 除了相互引用对方之外再无其他引用，但是因为它们的相互引用，导致两者的引用计数都不为 0，那么 JVM 就无法回收它们，导致内存浪费。

### 可达性分析算法

这个算法的基本思想是通过一系列称为 **“GC Roots”** 的对象作为起点，从这些节点开始向下搜索，节点所走过的路径称为 **引用链**，当一个对象到 GC Roots 没有任何引用链相连的话，则证明此对象是不可用的，需要被 JVM 回收。

![image.png](https://s2.loli.net/2025/09/13/QL7tlf39kimo8xZ.png)

上图中 `obj4`、`obj5`、`obj6` GC Roots 不可达，会被 JVM 回收。

通过可达性分析算法，解决了上面引用计数法的 “循环依赖” 问题。只要对象无法与 GC Root 建立直接 or 间接的连接，系统就会判定其为可回收对象。

既然这个方法是通过 GC Root 判断对象是否存活，那 GC Root 到底是什么？🤔

所谓 GC Roots，就是一组必须活跃的引用，**不是对象**，它们是程序运行时的起点，一切引用链的源头。在 Java 中 GC Roots 包括以下几种：

- 虚拟机栈中的引用（比如方法的参数、局部变量）
- 本地方法栈中 JNI 的引用
- 类静态变量
- 运行时常量池中的常量（String 或者 Class 类型）

![image.png](https://s2.loli.net/2025/09/27/Jm2lwBIu4KoNHVR.png)

更具体一点，在代码中我们如何辨认 GC Roots 呢？下面以上面提到的前两种为例。

1. **虚拟机栈中的引用（方法的参数、局部变量等）**

```java
public class StackReference {
    public void greet() {
        Object localVar = new Object(); // 这里的 localVar 是一个局部变量，存在于虚拟机栈中
        System.out.println(localVar.toString());
    }

    public static void main(String[] args) {
        new StackReference().greet();
    }
}
```

在 `greet()` 方法中，localVar 是一个局部变量，存在于虚拟机栈中，可以被认为是 GC Roots。在该方法执行期间，localVar 引用的对象是活跃的，因为它们是从 GC Root 出发可达的。当 `greet()` 方法执行完毕，localVar 作用域结束，**如果没有其他引用指向这些对象**，它们就可以被视作垃圾进行回收。

2. 本地方法栈中 JNI 的引用

JNI（Java Native Interface） 是  Java 提供的一种机制，允许 Java 代码调用本地代码（C/C++）。和调用 Java 方法类似，当调用本地方法时，虚拟机会通过 **动态链接** 直接调用指定的本地方法。

```java
// 假设的JNI方法
public native void nativeMethod();

// 假设在C/C++中实现的本地方法
/*
 * Class:     NativeExample
 * Method:    nativeMethod
 * Signature: ()V
 */
JNIEXPORT void JNICALL Java_NativeExample_nativeMethod(JNIEnv *env, jobject thisObj) {
    jobject localRef = (*env)->NewObject(env, ...); // 在本地方法栈中创建JNI引用
    // localRef 引用的Java对象在本地方法执行期间是活跃的
}
```

比如上面的代码，在本地代码（Java_NativeExample_nativeMethod）中，localRef 是对 Java 对象的一个 JNI 引用，它在本地方法执行期间保持 Java 对象活跃，可被认为是 GC Roots。一旦这个本地方法执行完毕，除非 localRef 的引用是全局的，否则它指向的对象会被作为垃圾回收掉。

## 垃圾收集算法

垃圾收集算法 **负责完成垃圾回收**，主要包括：

1. 标记 - 清除算法
2. 标记 - 整理算法
3. 复制算法
4. 分代收集算法

这部分比较容易理解，不再过多赘述。

## 堆空间的分代

堆（Heap）是 JVM 中最大的一块内存区域，也是垃圾回收器管理的主要区域。

堆空间主要分为两个区域，**年轻代和老年代**，其中年轻代又分为 Eden 区和 Survivor 区，而 Survivor 区又分为 From 和 To 两个区。

![image.png](https://s2.loli.net/2025/09/27/CbKdkq7ocTzMeGm.png)

### Eden 区

绝大多数对象存活时间并不会很长，因此 Java 对象在创建后会优先在 Eden 区进行内存分配，当 Eden 区没有足够空间时，JVM 会发起一次 **Minor GC**。

Minor GC 后，Eden 区中绝大部分对象会被回收，存活下来的对象会进到 From Survivor 区，如果 From 区不够，则直接进入 To 区。

### Survivor 区

**Q1：为什么需要 Survivor 区，直接 Eden 到老年代不好吗？为什么还需要加这么一层？**

由于 Eden 区的 Minor GC 进行得比较频繁，如果没有 Survivor 区，存活的对象就会直接进入老年代，这样的话老年代很快就会被塞满，从而触发 Major GC，导致 STW，严重影响程序性能。

同时，有些对象虽然不会在 Minor GC 被回收，但也不会存活的太久，这时候直接放到老年代不太合适。所以 Survivor 存在的意义是 **减少被送到老年代的对象**，进而减少 Major GC 的发生。

**Q2：Survivor 区为什么需要被划分成 From 和 To 两个区域？**

Survivor 区被划分为两个区域，主要是为了高效地实施 **复制算法**，避免内存碎片，提升垃圾回收（尤其是 Minor GC）的效率。

具体来说，每次 Minor GC 时，JVM 会将 Eden 区和一个 Survivor 区（From）中仍然存活的对象复制到另一个 **空的** Survivor 区（To）。复制完成后，Eden 和 From 会被完全清空，此时，**From 和 To 的角色会进行交换**，原来的 To 区编程下一次 GC 的 From 区，原来的 From 区则变为新的空 To 区。

**如果只有一块 Survivor 区**：

- Minor GC 后，Eden 和 Survivor 中都会有存活和死亡的对象交错存在
- 若要清理 Survivor 中的垃圾，可能需要用 **标记 - 清除** 算法，产生内存碎片；就算采用 **标记 - 整理** 算法，也会有 **性能损耗大、停顿时间长** 的问题
- 内存碎片会导致无法给大对象分配连续的空间，可能触发不必要的垃圾回收

### Old 区

老年代占堆空间的 2/3，只有在 Major GC/Full GC 时才会进行清理，每次 GC 都会触发 STW，内存越大，STW 的时间越长。

由于复制算法在对象存活率较高的老年代会进行多次赋值操作，效率低，所以老年代采用 **标记 - 整理** 算法。

另外，由于 **内存担保机制** 的存在，以下几种对象会直接进入老年代：

- 需要大量连续内存的对象
- 长期存活对象
- 动态对象年龄：不强制要求对象年龄到 15 岁再放入老年代，如果 Survivor 中某个年龄段及以上的对象总大小超过 Survivor 的一半，也会在下一次 GC 时晋升到老年代
