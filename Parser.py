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
            print(f"[DEBUG block] ln:{self.lex.ln} 当前token:{self.token}, 结束标记:{end}")
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
            peek_token = self.lex.peek_token()
            if peek_token.value in ['=', '+=', '-=', '*=', '/=', '//=']:
                return self.assignment()
            elif peek_token.type == '(':
                return self.fun_call()
            return self.expr()
        elif self.token.type in ['INT', 'FLT', 'STRING', 'BOOL']: # constant
            return self.expr()
        elif self.token.type == 'DEF' or self.token.type == 'PURE':
            is_pure = self.token.type == 'PURE'
            return self.defun(is_pure)
        elif self.token.type == 'IF':
            return self.if_statement()
        elif self.token.type == "RETURN":
            return self.return_statement()
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
        
        # 处理if块
        cond = self.expr()
        if self.token.type in ['THEN', 'NEWLINE'] or self.token.value == ';':
            self.eat('ANY')
        else:
            raise Exception('ParserError: expected THEN, NEWLINE or ;, got {}'.format(self.token))
        # if块的结束标记是ELIF、ELSE或END
        block = self.block(end=['ELIF', 'ELSE', 'END'])
        pair_list.append(CondPair(cond, block))
        
        # 处理所有elif块
        while self.token.type == 'ELIF':
            self.eat('ELIF')
            cond = self.expr()
            if self.token.type in ['THEN', 'NEWLINE'] or self.token.value == ';':
                self.eat('ANY')
            else:
                raise Exception('ParserError: expected THEN, NEWLINE or ;, got {}'.format(self.token))
            block = self.block(end=['ELIF', 'ELSE', 'END'])
            pair_list.append(CondPair(cond, block))
        
        # 处理else块
        else_block = None
        if self.token.type == 'ELSE':
            self.eat('ELSE')
            if self.token.type in ['THEN', 'NEWLINE'] or self.token.value == ';':
                self.eat('ANY')
            else:
                raise Exception('ParserError: expected THEN, NEWLINE or ;, got {}'.format(self.token))
            else_block = self.block(end=['END'])
        
        # 最后消费END
        if self.token.type == 'END':
            self.eat('END')
        return Condition(pair_list, else_block)
    
    def return_statement(self):
        self.eat('RETURN')
        expr = self.expr()
        return FunReturn(expr)

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
        token = self.token
        if token.type in ['INT', 'FLT']:
            self.eat('ANY')
            return Num(token)
        elif token.type == 'BOOL':
            self.eat('BOOL')
            return Bool(token)
        elif token.type == '(':
            self.eat('(')
            node = self.expr()
            self.eat(')')
            return node
        elif token.type == '[':
            # 数组字面量: [1, 2, 3]
            self.eat('[')
            elements = []
            # 处理空数组的情况
            if self.token.type == ']':
                self.eat(']')
                return Array(elements)
            # 解析第一个元素
            elements.append(self.expr())
            # 继续解析后面的元素，每个元素前面都有逗号
            while self.token.type == ',':
                self.eat(',')
                # 跳过可能的换行
                if self.token.type == 'NEWLINE':
                    self.eat('NEWLINE')
                elements.append(self.expr())
            # 现在应该遇到]了
            self.eat(']')
            return Array(elements)
        elif token.value in ['+', '-']:
            self.eat('OP')
            node = UnaryOp(op=token, expr=self.factor())  # 只递归调用factor，确保一元运算符只作用于下一个因子，优先级高于四则运算
            return node
        elif token.type == 'IDENT':
            next_token = self.lex.peek_token()
            if next_token.type == '(':
                return self.fun_call()
            elif next_token.type == '[':  # 数组访问: arr[0]
                array_node = self.variable()
                self.eat('[')
                index_node = self.expr()
                self.eat(']')
                return ArrayAccess(array_node, index_node)
            return self.variable()
        else:
            raise Exception("ParserError: unexpected factor {token}".format(token=self.token))

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
        
    def comparison(self):
        node = self.term()
        while self.token.value in ['==', '!=', '<', '>', '<=', '>=']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.term())
        while self.token.value in ['+', '-']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.term())
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