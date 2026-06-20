# Introduction
This is a python implementation of programming interpreter, supporting modern language features.

# Get Started
## Run with uv (recommended)
```shell
uv run python mylang.py --src source_file
```

## Run with native python
```shell
python mylang.py --src source_file
```

# Supported Features
## Core Language Features
- ✅ Variable assignment & basic arithmetic operations
- ✅ String manipulation & concatenation
- ✅ Boolean logic (and/or/not)
- ✅ Functions & recursive calls
- ✅ if-elif-else conditional statements (no `then` keyword required)
- ✅ while loop with break/continue support
- ✅ Typed arrays with negative indexing
- ✅ pure function memoization (automatic caching)

## Array Features
- Uniform type checking (all elements must be same type)
- 0-based indexing with negative index support
- Out-of-bounds error checking
- Definition: `arr = [1, 2, 3]` or `strs = ["a", "b", "c"]`

## Pure Function Memoization
Use `pure` keyword instead of `def` to mark pure functions, which automatically caches results:
```
pure fib(n)
    if n <= 1
        return n
    else
        return fib(n-1) + fib(n-2)
    end
end
```
Repeated calls with same arguments return cached results, drastically improving recursive function performance.

## Loop Control Statements
### break
跳出当前循环，终止循环执行：
```
i = 0
while i < 10
    if i == 5
        break
    end
    print(i)
    i = i + 1
end
```

### continue
跳过当前迭代，进入下一轮循环：
```
i = 0
while i < 10
    i = i + 1
    if i % 2 == 0
        continue  # 跳过偶数
    end
    print(i)
end
```

## Conditional Statements
Clean if-elif-else syntax with no `then` keyword required:
```
if score >= 90
    print("A")
elif score >= 80
    print("B")
elif score >= 60
    print("C")
else
    print("F")
end
```

# Development
## 已完成功能
- [x] 支持while循环（无do关键字：`while condition code_block end`）
- [x] 完善数组打印功能，支持直接print(arr)输出完整数组
- [x] 完成冒泡排序算法测试，验证while循环和数组操作的正确性
- [x] 实现break语句，用于循环中提前跳出
- [x] 修复fib函数中直接返回`fib(n-1) + fib(n-2)`的返回值处理逻辑
- [x] 支持continue语句
- [x] 移除then关键字依赖，简化if-elif-else语法

## 待实现功能
- [ ] 完善错误提示信息（包含行号列号）
- [ ] 支持for-in循环
- [ ] 添加更多内置函数（range/int/str/float等）
- [ ] 添加verbose模式控制调试日志输出

ref: https://ruslanspivak.com/