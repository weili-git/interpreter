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


class VarSymbol(Symbol):
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


class ScopedSymbolTable(object):
    def __init__(self, scope_name, scope_level, enclosing_scope):
        self._symbols = {}
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self._init_builtins()

    def _init_builtins(self):
        for _ in ['INT', 'FLT']:
            self.insert(BuiltinTypeSymbol(_))

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
        print('Insert: %s' % symbol.name)
        self._symbols[symbol.name] = symbol

    def lookup(self, name):
        print('Lookup: %s. (Scope name: %s)' % (name, self.scope_name))
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

    def visit_Program(self, node):
        print('ENTER scope: global')
        global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
            enclosing_scope=self.current_scope,
        )
        self.current_scope = global_scope

        self.visit(node.block)

        print(global_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: global')

    def visit_Block(self, node):
        for statement in node.statements:
            self.visit(statement)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Num(self, node):
        pass

    def visit_String(self, node):
        pass

    def visit_UnaryOp(self, node):
        self.visit(node.expr)

    def visit_NoOp(self, node):
        pass

    def visit_Assign(self, node):   # assign and declare
        self.visit(node.right)

        var_name = node.left.value
        var_symbol = VarSymbol(var_name)
        if not self.current_scope.lookup(var_name):
            self.current_scope.insert(var_symbol)

    def visit_Var(self, node):  # checking declaration
        var_name = node.value
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            raise Exception("SemanticError: identifier not found {}".format(node.token))

    def visit_Defun(self, node):
        proc_name = node.token.value
        proc_symbol = FunSymbol(proc_name)
        self.current_scope.insert(proc_symbol)

        print('ENTER scope: %s' % proc_name)
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

        print(procedure_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: %s' % proc_name)

    def visit_FunCall(self, node):
        for param in node.actual_params:
            self.visit(param)
        proc_symbol = self.current_scope.lookup(node.token.value)   # 查找函数定义
        node.proc_symbol = proc_symbol


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



