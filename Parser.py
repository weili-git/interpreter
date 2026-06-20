from Lexer import Lexer


class AST:
    """Abstract Syntax Tree"""
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class UnaryOp(AST):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr


class Num(AST):
    def __init__(self, token):
        """INT | FLT"""
        self.token = token
        self.value = token.value


class Bool(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class String(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Program(AST):
    def __init__(self, block):
        self.block = block


class Block(AST):
    def __init__(self, statements):
        self.statements = statements


class NoOp(AST):
    pass


class Assign(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value    # var_name


class Defun(AST):
    def __init__(self, token, formal_params, block):
        self.token = token
        self.formal_params = formal_params
        self.block = block


class Param(AST):
    def __init__(self, token):
        self.token = token


class FunCall(AST):
    def __init__(self, token, actual_params):
        self.token = token
        self.actual_params = actual_params
        # a reference to procedure declaration symbol
        self.proc_symbol = None


class FunReturn(AST):
    def __init__(self, expr):
        self.expr = expr


class CondPair(AST):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block


class Condition(AST):
    def __init__(self, pair_list, else_block):
        self.pair_list = pair_list
        self.else_block = else_block

class WhileLoop(AST):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block

class Break(AST):
    def __init__(self):
        pass

class Continue(AST):
    def __init__(self):
        pass

class MemberAccess(AST):
    def __init__(self, obj, method, args):
        self.object = obj      # 被访问的对象（数组变量）
        self.method = method   # 方法名（push/pop等）
        self.args = args       # 调用参数列表

class Array(AST):
    def __init__(self, elements):
        self.elements = elements

class ArrayAccess(AST):
    def __init__(self, array, index):
        self.array = array
        self.index = index


class Parser:
    def __init__(self, text):
        self.lex = Lexer(text)
        self.token = self.lex.next_token()

    def eat(self, token_type):
        """check type and advance"""
        # print(self.token)
        if self.token.type == token_type or token_type == 'ANY':
            self.token = self.lex.next_token()
        else:
            raise Exception('ParserError: expected {}, got {}'.format(token_type, self.token))

    def program(self):
        p = Program(self.block(end=['EOF']))
        self.eat('EOF')
        return p

    def block(self, end):
        statements = []
        while self.token.type not in end:
            # 处理所有连续的空行
            while self.token.type == 'NEWLINE':
                self.eat('NEWLINE')
            # 处理完空行后再次检查结束标记，避免处理完空行后才遇到结束标记仍进入解析
            if self.token.type in end:
                break
            # 再次检查，防止在处理空行的过程中token发生变化，现在如果是结束标记，直接break
            if self.token.type in end:
                break
            node = self.statement()
            if self.token.value == ';':
                self.eat('OP')
                statements.append(node)
            elif self.token.type == 'NEWLINE':
                self.eat('NEWLINE')
                statements.append(node)
            elif self.token.type in end:
                statements.append(node)
                break
            else:
                raise Exception("ParseError: unexpected end of block, ln: {} col: {}, {}".format(self.lex.ln, self.lex.col, self.token))
        # self.eat('ANY')
        # print("end of block")
        return Block(statements)

    def statement(self):
        if self.token.type == 'IDENT':
            # 先解析表达式，不管是变量还是数组访问，然后检查后面是否有赋值符号
            expr_node = self.expr()
            if self.token.value in ['=', '+=', '-=', '*=', '/=', '//=']:
                # 如果后面有赋值符号，说明这是一个赋值语句，左值是刚才解析的表达式（变量或数组访问）
                assign_op = self.token.value
                self.eat('OP')
                right = self.expr()
                return Assign(expr_node, assign_op, right)
            else:
                # 没有赋值符号，就是普通的表达式
                return expr_node
        elif self.token.type in ['INT', 'FLT', 'STRING', 'BOOL']: # constant
            return self.expr()
        elif self.token.type == 'DEF' or self.token.type == 'PURE':
            is_pure = self.token.type == 'PURE'
            return self.defun(is_pure)
        elif self.token.type == 'IF':
            return self.if_statement()
        elif self.token.type == 'WHILE':
            return self.while_statement()
        elif self.token.type == "RETURN":
            return self.return_statement()
        elif self.token.type == "BREAK":
            return self.break_statement()
        elif self.token.type == "CONTINUE":
            return self.continue_statement()
        else:
            return self.empty()

    def assignment(self):
        left = self.variable()
        assign_op = self.token.value
        self.eat('OP')
        right = self.expr()
        return Assign(left, assign_op, right)

    def fun_call(self):
        # func name
        token = self.variable()
        # func params
        actual_params = self.actual_parameters()
        return FunCall(token, actual_params)

    def defun(self, is_pure=False):
        if is_pure:
            self.eat('PURE')
        else:
            self.eat('DEF')
        token = self.variable()
        formal_params = []
        if self.token.type == '(':
            formal_params = self.formal_parameters()
        if self.token.type in ['NEWLINE', ';']:
            self.eat('ANY')
        block = self.block(end=['END'])
        self.eat('END')
        node = Defun(token, formal_params, block)
        node.is_pure = is_pure
        return node

    def formal_parameters(self):  # def foo(n)
        self.eat('(')
        fp = []
        while self.token.type == 'IDENT':
            fp.append(Param(self.variable()))
            if self.token.type == ')':
                break
            self.eat(',')
        self.eat(')')
        return fp

    def actual_parameters(self):  # foo(3)
        self.eat('(')
        params = []
        while self.token.type in ['INT', 'FLT', 'STRING', 'BOOL', 'IDENT']:
            params.append(self.expr())  # not Param
            if self.token.type == ')':
                break
            self.eat(',')
        self.eat(')')
        return params

    def if_statement(self):
        self.eat('IF')
        pair_list = []
        
        # 处理if块: if condition NEWLINE block ... END
        cond = self.expr()
        # 条件后必须是换行符或分号
        if self.token.type in ['NEWLINE'] or self.token.value == ';':
            self.eat('ANY')
        else:
            raise Exception('ParserError: expected NEWLINE or ; after if condition, got {}'.format(self.token))
        # if块的结束标记是ELIF、ELSE或END
        block = self.block(end=['ELIF', 'ELSE', 'END'])
        pair_list.append(CondPair(cond, block))
        
        # 处理所有elif块: elif condition NEWLINE block ... END
        while self.token.type == 'ELIF':
            self.eat('ELIF')
            cond = self.expr()
            if self.token.type in ['NEWLINE'] or self.token.value == ';':
                self.eat('ANY')
            else:
                raise Exception('ParserError: expected NEWLINE or ; after elif condition, got {}'.format(self.token))
            block = self.block(end=['ELIF', 'ELSE', 'END'])
            pair_list.append(CondPair(cond, block))
        
        # 处理else块: else NEWLINE block ... END
        else_block = None
        if self.token.type == 'ELSE':
            self.eat('ELSE')
            if self.token.type in ['NEWLINE'] or self.token.value == ';':
                self.eat('ANY')
            else:
                raise Exception('ParserError: expected NEWLINE or ; after else, got {}'.format(self.token))
            else_block = self.block(end=['END'])
        
        # 最后消费END
        if self.token.type == 'END':
            self.eat('END')
        return Condition(pair_list, else_block)
    
    def while_statement(self):
        self.eat('WHILE')
        cond = self.expr()
        if self.token.type in ['NEWLINE'] or self.token.value == ';':
            self.eat('ANY')
        else:
            raise Exception('ParserError: expected NEWLINE or ; after while condition, got {}'.format(self.token))
        # 内层的while block只有遇到END才会结束，不会提前遇到其他顶层语句结束
        block = self.block(end=['END'])
        if self.token.type == 'END':
            self.eat('END')
        return WhileLoop(cond, block)
    
    def return_statement(self):
        self.eat('RETURN')
        expr = self.expr()
        return FunReturn(expr)
        
    def break_statement(self):
        self.eat('BREAK')
        return Break()
        
    def continue_statement(self):
        self.eat('CONTINUE')
        return Continue()

    def cond_pair(self):
        cond = self.expr()
        if self.token.type in ['THEN', 'NEWLINE'] or self.token.value == ';':
            self.eat('ANY')
        else:
            raise Exception('ParserError: expected THEN, NEWLINE or ;, got {}'.format(self.token))
        block = self.block(end=['ELIF', 'ELSE', 'END'])
        return CondPair(cond, block)

    def term(self):
        if self.token.type == 'STRING':
            node = self.token
            self.eat('STRING')
            return String(node)
        node = self.factor()
        while self.token.value in ['*', '/', '//']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.factor())
        return node

    def factor(self):
        """原始的factor方法，保持和项目代码完全一致
        """
        token = self.token
        if token.value in ['+', '-', 'not', '!']:
            self.eat('OP')
            node = UnaryOp(op=token, expr=self.factor())
            return node
        if token.type in ['INT', 'FLT']:
            self.eat('ANY')
            return Num(token)
        if token.type == 'BOOL':
            self.eat('BOOL')
            return Bool(token)
        if token.type == 'STRING':
            self.eat('STRING')
            return String(token)
        if token.type == '(':
            self.eat('(')
            node = self.expr()
            self.eat(')')
            return node
        if token.type == '[':
            self.eat('[')
            elements = []
            if self.token.type == ']':
                self.eat(']')
                return Array(elements)
            elements.append(self.expr())
            while self.token.type == ',':
                self.eat(',')
                if self.token.type == 'NEWLINE':
                    self.eat('NEWLINE')
                elements.append(self.expr())
            self.eat(']')
            return Array(elements)
        if token.type == 'IDENT':
            var_node = Var(token)
            self.eat('IDENT')
            # 循环处理所有后缀操作符
            while True:
                # 数组访问：nums[0]
                if self.token.type == '[':
                    self.eat('[')
                    index_expr = self.expr()
                    self.eat(']')
                    var_node = ArrayAccess(var_node, index_expr)
                # 成员方法调用：nums.push(4)
                elif self.token.type == 'DOT':
                    self.eat('DOT')
                    if self.token.type != 'IDENT':
                        raise Exception(f"ParserError: 点号后需要标识符（方法名），但得到了 {self.token}")
                    method_name = self.token.value
                    self.eat('IDENT')
                    # 方法调用需要括号
                    if self.token.type == '(':
                        self.eat('(')
                        args = []
                        if self.token.type != ')':
                            args.append(self.expr())
                            while self.token.value == ',':
                                self.eat(',')
                                args.append(self.expr())
                        self.eat(')')
                        var_node = MemberAccess(var_node, method_name, args)
                    else:
                        raise Exception(f"ParserError: 不支持的成员访问 '.{method_name}'，当前仅支持方法调用")
                # 普通函数调用：fib(10)
                elif self.token.type == '(':
                    self.eat('(')
                    actual_params = []
                    if self.token.type != ')':
                        actual_params.append(self.expr())
                        while self.token.value == ',':
                            self.eat(',')
                            actual_params.append(self.expr())
                    self.eat(')')
                    var_node = FunCall(token, actual_params)
                else:
                    break
            return var_node
        raise Exception("ParserError: unexpected factor {}".format(self.token))

    def operator(self):
        token = self.token
        self.eat('OP')
        return token

    def expr(self):
        node = self.logical_or()
        return node
        
    def logical_or(self):
        node = self.logical_and()
        while self.token.value in ['or', '||']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.logical_and())
        return node
        
    def logical_and(self):
        node = self.comparison()
        while self.token.value in ['and', '&&']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.comparison())
        return node
        
    def addition_subtraction(self):
        node = self.multiplication_division()
        while self.token.value in ['+', '-']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.multiplication_division())
        return node

    def multiplication_division(self):
        node = self.factor()
        while self.token.value in ['*', '/', '//', '%']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.factor())
        return node

    def comparison(self):
        node = self.addition_subtraction()
        while self.token.value in ['==', '!=', '<', '>', '<=', '>=']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.addition_subtraction())
        return node

    def variable(self):
        node = Var(self.token)
        self.eat('IDENT')
        return node

    def empty(self):
        return NoOp()

    def parse(self):
        tree = self.program()
        return tree