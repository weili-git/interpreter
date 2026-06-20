# Introduction
This is a python implementation of programming interpreter, supporting modern language features.

# Get Started
## Run with uv (recommended)
```shell
uv run python mylang.py --src test/comprehensive.txt
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
- ✅ if-elif-else conditional statements
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
    if n <= 1 then
        n
    else
        fib(n-1) + fib(n-2)
    end
end
```
Repeated calls with same arguments return cached results, drastically improving recursive function performance.

# Development
## 待实现功能
- [x] 支持while循环（无do关键字：`while condition code_block end`）
- [x] 完善数组打印功能，支持直接print(arr)输出完整数组
- [x] 完成冒泡排序算法测试，验证while循环和数组操作的正确性
- [ ] 实现break语句，用于循环中提前跳出
- [ ] 修复fib函数中直接返回`fib(n-1) + fib(n-2)`的返回值处理逻辑
- [ ] 支持continue语句
- [ ] 完善错误提示信息
ref: https://ruslanspivak.com/