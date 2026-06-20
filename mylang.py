from Semantic import *
import argparse


class FunReturn(Exception):
    def __init__(self, value):
        self.value = value

class Interpreter(NodeVisitor):
    def __init__(self):
        self.call_stack = CallStack()
        self.function_cache = {}
        
    def format_val(self, v):
        """统一格式化值的输出，字符串添加双引号边界，数组也能正确打印"""
        if isinstance(v, str):
            return f'"{v}"'
        elif isinstance(v, list):
            # 递归格式化数组元素，支持嵌套数组
            formatted_elements = [self.format_val(elem) for elem in v]
            return f'[{", ".join(formatted_elements)}]'
        elif v is None:
            return 'None'
        return str(v)

    def visit_NoOp(self, node):     # dummy node
        return "No operation."

    def visit_BinOp(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)
        result = None
        
        if node.op.value == '+':
            result = left_val + right_val
        elif node.op.value == '-':
            result = left_val - right_val
        elif node.op.value == '*':
            result = left_val * right_val
        elif node.op.value == '/':
            result = left_val / right_val
        elif node.op.value == '//':
            result = left_val // right_val
        elif node.op.value == '==':
            result = left_val == right_val
        elif node.op.value == '!=':
            result = left_val != right_val
        elif node.op.value == '<':
            result = left_val < right_val
        elif node.op.value == '>':
            result = left_val > right_val
        elif node.op.value == '<=':
            result = left_val <= right_val
        elif node.op.value == '>=':
            result = left_val >= right_val
        elif node.op.value in ['and', '&&']:
            result = left_val and right_val
        elif node.op.value in ['or', '||']:
            result = left_val or right_val
            
        print(f"[表达式] {self.format_val(left_val)} {node.op.value} {self.format_val(right_val)} = {self.format_val(result)}")
        return result
        # elif node.op.value == '**':
        #     return self.visit(node.left) ** self.visit(node.right)

    def visit_UnaryOp(self, node):
        op = node.op.value
        if op == '+':
            return +self.visit(node.expr)
        if op == '-':
            return -self.visit(node.expr)
        if op == '!':
            return not self.visit(node.expr)

    def visit_Num(self, node):
        return node.value

    def visit_Bool(self, node):
        return node.value

    def visit_String(self, node):
        return node.value

    def visit_Array(self, node):
        # 计算数组所有元素的值
        values = []
        for element in node.elements:
            values.append(self.visit(element))
        return values

    def visit_ArrayAccess(self, node):
        # 获取数组的值
        array = self.visit(node.array)
        if not isinstance(array, list):
            raise Exception(f"RuntimeError: '{node.array.value}' 不是一个数组，无法进行索引访问。")
        
        # 获取索引值
        index = self.visit(node.index)
        if not isinstance(index, (int, float)):
            raise Exception(f"RuntimeError: 数组索引必须是数值类型，当前类型: {type(index).__name__}")
        
        # 转换为整数索引
        index = int(index)
        array_len = len(array)
        
        # 支持负索引
        if index < 0:
            index += array_len
        
        # 检查是否越界
        if index < 0 or index >= array_len:
            raise Exception(f"RuntimeError: 数组索引越界，数组长度: {array_len}, 访问索引: {index}")
            
        return array[index]

    def visit_Program(self, node):

        ar = ActivationRecord(
            name="mylang",
            type=ARType.PROGRAM,
            nesting_level=1,
        )
        self.call_stack.push(ar)
        # 构建内置函数？
        self.visit(node.block)
        self.call_stack.pop()

    def visit_Block(self, node):
        last_result = None
        for statement in node.statements:
            result = self.visit(statement)
            # 对于独立的表达式（非语句类节点），统一以[表达式]标签输出其值
            if isinstance(statement, (Var, Num, Bool, String, ArrayAccess, BinOp, UnaryOp)):
                print(f"[表达式] {self.format_val(result)}")
            last_result = result
        return last_result

    def visit_Assign(self, node):
        assign_value = self.visit(node.right)
        ar = self.call_stack.peek()
        # 处理复合赋值运算符
        if node.op == '=':
            pass
        elif node.op == '+=':
            assign_value += self.visit(node.left)
        elif node.op == '-=':
            assign_value -= self.visit(node.left)
        elif node.op == '*=':
            assign_value *= self.visit(node.left)
        elif node.op == '/=':
            assign_value /= self.visit(node.left)
        elif node.op == '//=':
            assign_value //= self.visit(node.left)
        else:
            print("Not an assignment operator: ", node.op)
        # 处理数组元素赋值
        if isinstance(node.left, ArrayAccess):
            # 处理数组元素赋值: arr[i] = value，ArrayAccess的属性是array和index
            array_node = node.left.array
            index_node = node.left.index
            array_name = array_node.value
            index = self.visit(index_node)
            target_array = ar[array_name]
            array_len = len(target_array)
            # 支持负索引
            if index < 0:
                index += array_len
            # 检查索引越界
            if index < 0 or index >= array_len:
                raise Exception(f"RuntimeError: 数组索引越界，数组长度: {array_len}, 访问索引: {index}")
            target_array[index] = assign_value
            print(f"[赋值语句] {array_name}[{index}] = {self.format_val(assign_value)}")
        elif isinstance(node.left, Var):
            # 普通变量赋值
            var_name = node.left.value
            ar[var_name] = assign_value
            print(f"[赋值语句] {var_name} = {self.format_val(assign_value)}")
        return assign_value

    def visit_Var(self, node):
        var_name = node.value
        ar = self.call_stack.peek()
        var_value = ar[var_name]
        if var_value is None:   # right now, 'None' is not assignable
            raise Exception("Undefined identifier: " + var_name)
        else:
            return var_value

    def visit_FunCall(self, node):
        proc_name = node.token.value
        # 处理内置print函数
        if proc_name == 'print':
            # 支持打印多个参数
            values = []
            for param in node.actual_params:
                values.append(self.format_val(self.visit(param)))
            print(f"[打印输出] {' '.join(values)}")
            return None
        # 处理内置len函数，获取数组长度
        elif proc_name == 'len':
            if len(node.actual_params) != 1:
                raise Exception(f"RuntimeError: len()函数需要1个参数，当前传入{len(node.actual_params)}个")
            arg = self.visit(node.actual_params[0])
            if not isinstance(arg, list):
                raise Exception(f"RuntimeError: len()函数只支持数组类型，当前类型: {type(arg).__name__}")
            return len(arg)
        elif proc_name == 'print_arr':
            if len(node.actual_params) != 1:
                raise Exception(f"RuntimeError: print_arr()函数需要1个数组参数，当前传入{len(node.actual_params)}个")
            arg = self.visit(node.actual_params[0])
            if not isinstance(arg, list):
                raise Exception(f"RuntimeError: print_arr()函数只支持数组类型，当前类型: {type(arg).__name__}")
            # 格式化打印数组元素
            elements_str = ', '.join(self.format_val(elem) for elem in arg)
            print(f"[打印数组] [{elements_str}]")
            return None
        cur_ar = self.call_stack.peek()
        proc_symbol = cur_ar[proc_name]

        # 格式化实际参数的显示
        args = [self.visit(arg) for arg in node.actual_params]
        args_str = ", ".join(self.format_val(arg) for arg in args)
        print(f"[函数调用] {proc_name}({args_str})")
        
        # 正确获取proc_symbol的is_pure属性，纯函数才检查缓存
        is_pure = getattr(proc_symbol, 'is_pure', False)
        if is_pure:
            cache_key = (proc_name, tuple(args))
            if cache_key in self.function_cache:
                print(f"[缓存命中] {proc_name}{args} = {self.format_val(self.function_cache[cache_key])}")
                return self.function_cache[cache_key]
        
        ar = ActivationRecord(
            name=proc_name,
            type=ARType.PROCEDURE,
            nesting_level=proc_symbol.scope_level + 1
        )
        # 修复递归调用问题：将当前函数添加到新的活动记录中，让递归调用能找到函数本身
        ar[proc_name] = proc_symbol

        formal_params = proc_symbol.formal_params
        actual_params = node.actual_params
        for param_symbol, argument_node, arg_value in zip(formal_params, actual_params, args):
            ar[param_symbol.token.value] = arg_value
        self.call_stack.push(ar)

        return_value = None
        try:
            return_value = self.visit(proc_symbol.block_ast)
        except FunReturn as fr:
            return_value = fr.value
        finally:
            self.call_stack.pop()
        # 只有纯函数才将计算结果存入缓存，使用前面定义的is_pure变量
        if is_pure:
            cache_key = (proc_name, tuple(args))
            self.function_cache[cache_key] = return_value
        print(f"[函数返回] {proc_name}() = {self.format_val(return_value)}")
        return return_value
    
    def visit_FunReturn(self, node):
        return_value = self.visit(node.expr)
        raise FunReturn(return_value)

    def visit_Defun(self, node):  ###
        proc_name = node.token.value
        # 读取节点的is_pure属性，直接设置到proc_symbol，绕过语义分析的传递问题
        node_is_pure = getattr(node, 'is_pure', False)
        # 格式化参数列表的显示
        params = [p.token.value for p in node.formal_params]
        params_str = ", ".join(params)
        print(f"[函数定义] {proc_name}({params_str})")
        
        proc_symbol = FunSymbol(proc_name)
        proc_symbol.formal_params = node.formal_params
        proc_symbol.block_ast = node.block
        # 直接在这里设置is_pure，确保解释器能读取到，彻底解决属性传递问题
        proc_symbol.is_pure = node_is_pure

        current_ar = self.call_stack.peek()
        current_ar[proc_name] = proc_symbol
        return None

    def visit_CondPair(self, node):
        if self.visit(node.cond) not in [0, False, None]:
            return self.visit(node.block)
        else:
            return None

    def visit_Condition(self, node):
        print("[条件语句开始] if-elif-else")
        result = None
        for i, pair in enumerate(node.pair_list):
            cond_result = self.visit(pair.cond)
            print(f"[条件判断] {'if' if i==0 else 'elif'} 条件结果: {self.format_val(cond_result)}")
            if cond_result not in [0, False, None]:
                print(f"[条件分支] 进入{'if' if i==0 else 'elif'}分支")
                result = self.visit(pair.block)
                break
        else:
            if node.else_block:
                print("[条件分支] 进入else分支")
                result = self.visit(node.else_block)
        print("[条件语句结束]")
        return result

    def visit_WhileLoop(self, node):
        print("[循环开始] while循环")
        loop_count = 0
        max_loops = 10000  # 防止无限循环
        while True:
            cond_result = self.visit(node.cond)
            if cond_result in [0, False, None] or loop_count >= max_loops:
                if loop_count >= max_loops:
                    print("[循环警告] 达到最大循环次数，强制退出")
                break
            print(f"[循环执行] 第{loop_count+1}次迭代")
            self.visit(node.block)
            loop_count += 1
        print(f"[循环结束] 共执行{loop_count}次迭代")
        return None

    def interpret(self, tree):
        return self.visit(tree)


import os

def parse_file(path):
    if not os.path.exists(path):
        print(f"错误：文件 '{path}' 不存在！")
        return
    print(f"正在解析文件: {path}")
    with open(path) as f:
        text = f.read()
        print("文件内容读取成功，开始解析...")
        tree = Parser(text).parse()
        print("语法分析完成，开始语义分析...")
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.visit(tree)
        print("语义分析完成，开始执行...")
        print("\n执行结果:")
        interpreter = Interpreter()
        interpreter.interpret(tree)
        print("\n执行完成！")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="parse source file")
    parser.add_argument("--src", type=str, default="test/test04.txt")

    args = parser.parse_args()
    parse_file(args.src)

# https://github.com/rspivak/lsbasi/blob/master/part19/spi.py