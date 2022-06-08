class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.read_pos = 0
        self.keywords = {}
        self.symbols = ['+', '-', '*', '/']
        self.ch = self.text[self.pos]

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.ch = None  # Indicates end of input
        else:
            self.ch = self.text[self.pos]

    def skip_whitespace(self):
        while self.pos < len(self.text) and self.ch.isspace():
            self.advance()

    def integer(self):
        result = ''     # str -> int
        while self.pos < len(self.text) and self.ch.isdigit():
            result += self.ch
            self.advance()
        return int(result)

    def next_token(self):
        self.skip_whitespace()

        if self.pos > len(self.text) - 1:
            return Token('EOF', None)

        self.ch = self.text[self.pos]

        if self.ch.isdigit():
            token = Token('INT', self.integer())
            return token

        if self.ch in self.symbols:
            ch = self.ch
            self.advance()
            return Token('OP', ch)

        if self.ch == '(':
            self.advance()
            return Token('(', None)

        if self.ch == ')':
            self.advance()
            return Token(')', None)

        raise Exception("Invalid Token")


class AST:
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
        self.token = token
        self.value = token.value


class Parser:
    def __init__(self, text):
        """
            expr: term((+|-)term)*
            term: factor((*|/)factor)*
            factor: INT | LPAREN expr RPAREN
        """
        self.lex = Lexer(text)
        self.token = self.lex.next_token()

    def eat(self, token_type):  # check type and advance
        print(self.token)
        if self.token.type == token_type:
            self.token = self.lex.next_token()
        else:
            raise Exception("Invalid Syntax: expected %s, got %s" % (token_type, self.token.type))

    def term(self):
        node = self.factor()
        while self.token.value in ['*', '/']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.factor())
        return node

    def factor(self):
        token = self.token
        if token.type == 'INT':
            self.eat('INT')
            return Num(token)
        elif token.type == '(':
            self.eat('(')
            node = self.expr()
            self.eat(')')
            return node
        elif token.value in ['+', '-']:
            self.eat('OP')
            node = UnaryOp(op=token, expr=self.expr())
            return node

    def operator(self):
        token = self.token
        self.eat('OP')
        return token

    def expr(self):
        node = self.term()
        while self.token.value in ['+', '-']:
            op = self.operator()
            node = BinOp(left=node, op=op, right=self.term())
        return node


class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__    # visit_BinOp ~ visit_UnaryOp
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class Interpreter(NodeVisitor):
    def __init__(self, text):
        self.parser = Parser(text)

    def visit_BinOp(self, node):
        if node.op.value == '+':
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.value == '-':
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.value == '*':
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.value == '/':
            return self.visit(node.left) / self.visit(node.right)

    def visit_UnaryOp(self, node):
        op = node.op.value
        if op == '+':
            return +self.visit(node.expr)
        if op == '-':
            return -self.visit(node.expr)

    def visit_Num(self, node):
        return node.value

    def interpret(self):
        tree = self.parser.expr()
        self.parser.eat('EOF')
        return self.visit(tree)


def main():
    while True:
        try:
            text = input('>>')
        except EOFError:
            break
        if not text:
            continue
        if text == 'q':
            break
        interpreter = Interpreter(text)
        result = interpreter.interpret()
        print(result)


if __name__ == '__main__':
    main()

