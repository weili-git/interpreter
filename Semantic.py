from Parser import *


class NodeVisitor:
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__    # 巧妙
        visitor = getattr(self, method_name, self.generic_visit)
        # print(method_name)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class Symbol:
    def __init__(self, name, type=None):
        """class name indicate its category"""
        self.name = name
        self.type = type
        self.scope_level = 0


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<{class_name}(name='{name}')>".format(class_name=self.__class__.__name__, name=self.name,)


class BuiltinFunSymbol(Symbol):
    def __init__(self, name, formal_params=None):
        super(BuiltinFunSymbol, self).__init__(name)
        self.formal_params = [] if formal_params is None else formal_params
        self.block_ast = None

    def __str__(self):
        return "<{class_name}(name='{name}', parameters='{parameters}')>".format(class_name=self.__class__.__name__,
                                                                                 name=self.name,
                                                                                 parameters=self.formal_params)
    __repr__ = __str__


class VarSymbol(Symbol):  # 弱类型
    def __init__(self, name):
        """<VarSymbol(name='x', type='INT')>"""
        super().__init__(name)

    def __str__(self):
        return "<{}(name='{}')>".format(self.__class__.__name__, self.name, )

    __repr__ = __str__


class FunSymbol(Symbol):
    def __init__(self, name, formal_params=None):
        """<FunSymbol(name='foo', parameters=...)>"""
        super(FunSymbol, self).__init__(name)
        self.formal_params = [] if formal_params is None else formal_params
        self.block_ast = None

    def __str__(self):
        return '<{}(name={}, parameters={})>'.format(self.__class__.__name__, self.name, self.formal_params, )

    __repr__ = __str__


class ArraySymbol(Symbol):
    def __init__(self, name, element_type, elements=None):
        super().__init__(name)
        self.element_type = element_type  # 'number', 'string', 'bool', None(空数组)
        self.elements = elements or []

    def __str__(self):
        return f"<ArraySymbol(name='{self.name}', element_type='{self.element_type}')>"
    __repr__ = __str__


class ScopedSymbolTable(object):
    def __init__(self, scope_name, scope_level, enclosing_scope):
        self._symbols = {}
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self._init_builtins()

    def _init_builtins(self):
        for _ in ['INT', 'FLT', 'STRING', 'BOOL']:
            self.insert(BuiltinTypeSymbol(_))
        self.insert(BuiltinFunSymbol('print'))  # todo

    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
            ('Scope name', self.scope_name),
            ('Scope level', self.scope_level),
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, value))
            for key, value in self._symbols.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    __repr__ = __str__

    def insert(self, symbol):
        if symbol.name in self._symbols.keys():
            # 同一作用域内不允许任何重复名称，无论是变量还是函数
            existing = self._symbols[symbol.name]
            raise ValueError(f"标识符 '{symbol.name}' 已经存在，不能重复定义。原定义为: {existing}")
        self._symbols[symbol.name] = symbol

    def lookup(self, name):
        # 'symbol' is either an instance of the Symbol class or None
        symbol = self._symbols.get(name)

        if symbol is not None:
            return symbol

        # recursively go up the chain and lookup the name
        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(name)


class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        """
        Static semantic checks:
            declaration checking, argument checking, (type checking)
        """
        self.current_scope = None
        self.in_loop = False  # 标记是否在循环内部，用于检查break/continue的合法性

    def visit_Program(self, node):
        global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
            enclosing_scope=self.current_scope,
        )
        self.current_scope = global_scope

        self.visit(node.block)

        self.current_scope = self.current_scope.enclosing_scope

    def visit_Block(self, node):
        for statement in node.statements:
            self.visit(statement)

    def visit_WhileLoop(self, node):
        # 保存之前的循环状态
        prev_in_loop = self.in_loop
        # 进入循环，设置in_loop为True
        self.in_loop = True
        # 检查循环条件的语义
        self.visit(node.cond)
        # 检查循环体的语义
        self.visit(node.block)
        # 恢复之前的循环状态
        self.in_loop = prev_in_loop

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Num(self, node):
        pass

    def visit_Bool(self, node):
        pass

    def visit_String(self, node):
        pass

    def visit_Array(self, node):
        element_type = None
        # 检查数组元素类型是否一致
        for element in node.elements:
            self.visit(element)  # 先处理元素本身的语义检查
            # 推断元素类型
            if isinstance(element, Num):
                current_type = 'number'
            elif isinstance(element, String):
                current_type = 'string'
            elif isinstance(element, Bool):
                current_type = 'bool'
            else:
                # 变量或表达式，暂时支持，运行时会再次检查
                current_type = None
                
            if element_type is None:
                element_type = current_type
            elif element_type != current_type and current_type is not None:
                raise Exception(f"SemanticError: 数组元素类型不一致，期望类型 '{element_type}'，但发现类型 '{current_type}'。")
        # 存储数组的元素类型，供后续使用
        node.element_type = element_type

    def visit_ArrayAccess(self, node):
        # 检查数组是否存在
        self.visit(node.array)  # 先检查数组变量是否已定义
        # 检查索引的类型
        self.visit(node.index)
        # 索引必须是数值类型
        index_node = node.index
        if not isinstance(index_node, (Num, Var, BinOp, UnaryOp)):  # 支持一元运算符，如-1
            raise Exception(f"SemanticError: 数组索引必须是数值类型。节点: {index_node}")

    def visit_UnaryOp(self, node):
        self.visit(node.expr)

    def visit_NoOp(self, node):
        pass

    def visit_Assign(self, node):   # assign and declare
        self.visit(node.right)
        # 处理不同类型的左值
        if isinstance(node.left, Var):
            # 普通变量赋值，原有逻辑
            var_name = node.left.value
            # 如果右值是数组，创建ArraySymbol，否则创建VarSymbol
            if isinstance(node.right, Array):
                array_symbol = ArraySymbol(var_name, node.right.element_type, node.right.elements)
                if not self.current_scope.lookup(var_name):
                    self.current_scope.insert(array_symbol)
            else:
                var_symbol = VarSymbol(var_name)
                if not self.current_scope.lookup(var_name):  # 分开查找变量和函数？
                    self.current_scope.insert(var_symbol)
        elif isinstance(node.left, ArrayAccess):
            # 数组元素赋值，先检查数组本身是否定义，再检查索引的语义
            self.visit(node.left.array)
            self.visit(node.left.index)

    def visit_Var(self, node):  # checking declaration
        var_name = node.value
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            raise Exception(f"SemanticError: 变量 '{var_name}' 未定义，请先声明后再使用。节点信息: {node.token}")

    def visit_Defun(self, node):
        proc_name = node.token.value
        proc_symbol = FunSymbol(proc_name)
        # 将纯函数标记传递到符号表中
        proc_symbol.is_pure = getattr(node, 'is_pure', False)
        self.current_scope.insert(proc_symbol)

        # Scope for parameters and local variables
        procedure_scope = ScopedSymbolTable(
            scope_name=proc_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )
        self.current_scope = procedure_scope

        # Insert parameters into the procedure scope
        for param in node.formal_params:
            param_name = param.token.value
            var_symbol = VarSymbol(param_name)
            self.current_scope.insert(var_symbol)
            proc_symbol.formal_params.append(var_symbol)

        self.visit(node.block)

        self.current_scope = self.current_scope.enclosing_scope

    def visit_FunCall(self, node):
        for param in node.actual_params:
            self.visit(param)
        proc_name = node.token.value
        # 内置函数不需要提前定义
        builtin_functions = ['print', 'len']
        if proc_name in builtin_functions:
            return
        proc_symbol = self.current_scope.lookup(proc_name)   # 查找函数定义
        if proc_symbol is None:
            raise Exception(f"SemanticError: 函数 '{proc_name}' 未定义，请先定义后再调用。节点信息: {node.token}")
        # 检查是否确实是函数类型
        if not isinstance(proc_symbol, FunSymbol):
            raise Exception(f"SemanticError: '{proc_name}' 不是一个函数，无法调用。它的类型是: {type(proc_symbol).__name__}")
        node.proc_symbol = proc_symbol

    def visit_FunReturn(self, node):
        self.visit(node.expr)
        
    def visit_CondPair(self, node):
        self.visit(node.cond)
        self.visit(node.block)
        
    def visit_Condition(self, node):
        for pair in node.pair_list:
            self.visit(pair)
        if node.else_block:
            self.visit(node.else_block)
            
    def visit_Break(self, node):
        # 检查break语句是否在循环内部使用
        if not self.in_loop:
            raise Exception("SemanticError: break语句只能在循环内部使用")
            
    def visit_Continue(self, node):
        # 检查continue语句是否在循环内部使用
        if not self.in_loop:
            raise Exception("SemanticError: continue语句只能在循环内部使用")
            
    def visit_MemberAccess(self, node):
        # 先检查被访问的对象是否合法
        self.visit(node.object)
        # 检查方法名是否受支持
        supported_methods = ['push', 'pop', 'len']
        if node.method not in supported_methods:
            raise Exception(f"SemanticError: 不支持的数组方法 '{node.method}'，支持的方法有: {supported_methods}")
        # 检查参数数量是否正确
        if node.method == 'push' and len(node.args) != 1:
            raise Exception("SemanticError: push()方法需要且仅需要1个参数")
        if node.method == 'pop' and len(node.args) != 0:
            raise Exception("SemanticError: pop()方法不需要参数")
        if node.method == 'len' and len(node.args) != 0:
            raise Exception("SemanticError: len()方法不需要参数")
        # 检查所有参数的语义
        for arg in node.args:
            self.visit(arg)


class CallStack:
    def __init__(self):
        self._records = []

    def push(self, ar):
        self._records.append(ar)

    def pop(self):
        return self._records.pop()

    def peek(self):
        return self._records[-1]

    def __str__(self):
        s = '\n'.join(repr(ar) for ar in reversed(self._records))
        s = f'CALL STACK\n{s}\n'
        return s

    def __repr__(self):
        return self.__str__()


class ARType:
    PROGRAM = 'PROGRAM'
    PROCEDURE = 'PROCEDURE'


class ActivationRecord:
    def __init__(self, name, type, nesting_level):
        self.name = name
        self.type = type
        self.nesting_level = nesting_level
        self.members = {}

    def __setitem__(self, key, value):
        self.members[key] = value

    def __getitem__(self, key):
        return self.members[key]

    def get(self, key):
        return self.members.get(key)

    def __str__(self):
        lines = [
            '{level}: {type} {name}'.format(
                level=self.nesting_level,
                type=self.type.value,
                name=self.name,
            )
        ]
        for name, val in self.members.items():
            lines.append(f'   {name:<20}: {val}')

        s = '\n'.join(lines)
        return s

    def __repr__(self):
        return self.__str__()