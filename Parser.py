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


class CondPair(AST):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block


class Condition(AST):
    def __init__(self, pair_list, else_block):
        self.pair_list = pair_list
        self.else_block = else_block


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
            if self.lex.peek_token().value == '=':
                return self.assignment()
            elif self.lex.peek_token().type == '(':
                return self.fun_call()
            return self.expr()
        elif self.token.type in ['INT', 'FLT', 'STRING', 'BOOL']:
            return self.expr()
        elif self.token.type == 'DEF':
            return self.defun()
        elif self.token.type == 'IF':
            return self.if_statement()
        else:
            return self.empty()

    def assignment(self):
        left = self.variable()
        op = self.eat('OP')     # =, +=, -=, ...
        right = self.expr()
        return Assign(left, op, right)

    def fun_call(self):
        token = self.variable()
        actual_params = self.actual_parameters()
        return FunCall(token, actual_params)

    def defun(self):
        self.eat('DEF')
        token = self.variable()
        formal_params = []
        if self.token.type == '(':
            formal_params = self.formal_parameters()
        if self.token.type in ['NEWLINE', ';']:
            self.eat('ANY')
        block = self.block(end=['END'])
        self.eat('END')
        return Defun(token, formal_params, block)

    def formal_parameters(self):
        self.eat('(')
        result = []
        while self.token.type == 'IDENT':
            result.append(Param(self.variable()))
            if self.token.type == ')':
                break
            self.eat(',')
        self.eat(')')
        return result

    def actual_parameters(self):
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
        pair_list = [self.cond_pair()]
        while self.token.type == 'ELIF':
            self.eat('ELIF')
            pair_list.append(self.cond_pair())
        else_block = None
        if self.token.type == 'ELSE':
            self.eat('ELSE')
            if self.token.type in ['THEN', 'NEWLINE'] or self.token.value == ';':
                self.eat('ANY')
            else:
                raise Exception('ParserError: expected THEN, NEWLINE or ;, got {}'.format(self.token))
            else_block = self.block(end=['END'])
        self.eat('END')
        return Condition(pair_list, else_block)

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
        elif token.value in ['+', '-']:
            self.eat('OP')
            node = UnaryOp(op=token, expr=self.expr())
            return node
        elif token.type == 'IDENT':
            if self.lex.peek_token().type == '(':
                return self.fun_call()
            return self.variable()
        else:
            raise Exception("ParserError: unexpected factor {token}".format(token=self.token))

    def operator(self):
        token = self.token
        self.eat('OP')
        return token

    def expr(self):
        node = self.term()
        while self.token.value in ['+', '-']:     # 实际上||,&&和!的优先级很低
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



