from collections import OrderedDict


class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return 'Token({type}, {value})'.format(type=self.type, value=repr(self.value))

    def __repr__(self):
        return self.__str__()


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.ch = self.text[self.pos]
        self.keywords = {'def', 'return', 'end', 'if', 'else'}
        self.operators = ['+', '-', '*', '/', '//', '**', '=', '==', ';', ':']

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.ch = None  # Indicates end of input
        else:
            self.ch = self.text[self.pos]

    def skip_whitespace(self):
        while self.pos < len(self.text) and self.ch.isspace():
            self.advance()

    def skip_comment(self):
        if self.ch == '#':
            while self.pos < len(self.text) and self.ch != '\n':
                self.advance()
            self.advance()  # jump over '\n'

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos > len(self.text) - 1:
            return None
        else:
            return self.text[peek_pos]

    def identifier(self):
        result = ''
        while self.pos < len(self.text) and self.ch.isalnum():  # alphabet and number
            result += self.ch
            self.advance()
        if result in self.keywords:
            return Token('KEYWORD', result)
        return Token('IDENT', result)

    def number(self):
        result = ''     # str -> int
        while self.pos < len(self.text) and self.ch.isdigit():
            result += self.ch
            self.advance()
        if self.ch == '.':
            result += self.ch
            self.advance()
            while self.pos < len(self.text) and self.ch.isdigit():
                result += self.ch
                self.advance()
            return Token('FLT', float(result))
        return Token('INT', int(result))

    def string(self):
        self.advance()
        result = ''
        while self.pos < len(self.text) and self.ch != '"':
            if self.ch == '\\':
                next = self.peek()
                if next == '"':
                    result += '"'
                elif next == '\\':
                    result += '\\'
                elif next == 'n':
                    result += '\n'
                else:
                    result += next
                self.advance()
                self.advance()
                continue
            result += self.ch
            self.advance()
        if self.ch != '"':
            raise Exception("Syntax Error: EOF while scanning the string literal")
        self.advance()
        return Token('STRING', result)

    def next_token(self):
        self.skip_whitespace()
        self.skip_comment()

        if self.pos > len(self.text) - 1:
            return Token('EOF', None)

        self.ch = self.text[self.pos]

        if self.ch.isalpha():
            return self.identifier()

        if self.ch.isdigit():
            return self.number()

        if self.ch == '"':
            return self.string()

        if self.ch in self.operators:
            ch = self.ch
            next = self.peek()
            if next and ch + next in self.operators:
                self.advance()
                self.advance()
                return Token('OP', ch + next)
            self.advance()
            return Token('OP', ch)

        if self.ch == '(':  # eat('(') is available
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
        """INT | FLT"""
        self.token = token
        self.value = token.value


class String(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Program(AST):
    def __init__(self, block):
        self.block = block


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
        self.value = token.value


class Defun(AST):
    def __init__(self, name, params, block):
        self.name = name
        self.params = params  # list of Param nodes
        self.block = block


class Param(AST):
    def __init__(self, var):
        self.var = var


class Parser:
    def __init__(self, text):
        self.lex = Lexer(text)
        self.token = self.lex.next_token()

    def eat(self, token_type):
        """check type and advance"""
        print(self.token)
        if self.token.type == token_type:
            self.token = self.lex.next_token()
        else:
            raise Exception("Invalid Syntax: expected %s, got %s" % (token_type, self.token.type))

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
        if token.type == 'INT':
            self.eat('INT')
            return Num(token)
        elif token.type == 'FLT':
            self.eat('FLT')
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
        elif token.type == 'IDENT':
            return self.variable()
        else:
            raise Exception("Syntax Error: null expr")

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

    def program(self):
        results = []
        while self.token.type != 'EOF':
            node = self.statement()
            if self.token.value == ';':
                self.eat('OP')
                results.append(node)
            else:
                raise Exception("Invalid Syntax: expected ;, got " + self.token.type)
        self.eat('EOF')
        return Program(results)

    def statement(self):
        if self.token.type == 'IDENT':
            return self.assignment()
        elif self.token.type in ['INT', 'FLT', 'STRING']:
            return self.expr()
        elif self.token.type == 'KEYWORD':
            if self.token.value == 'def':
                return self.defun()
            raise Exception("Not implemented keyword")
        else:
            return self.empty()     # important

    def defun(self):
        self.eat('KEYWORD')     # def
        # right now, no argument
        name = self.variable()  # def name {block} end
        params = []
        if self.token.type == '(':
            params = self.parameters()
        block = self.program()
        if self.token.value == 'end':
            self.eat('KEYWORD')
            return Defun(name, params, block)
        raise Exception("Invalid Syntax: expected end, got " + self.token.value)

    def parameters(self):
        self.eat('(')
        result = []
        while self.token.type == 'IDENT':
            result.append(Param(self.variable()))
            if self.token.type != ',':
                break
            self.eat(',')
        self.eat(')')
        return result

    def empty(self):
        return NoOp()

    def assignment(self):
        left = self.variable()
        op = self.token
        if op.value == '=':
            self.eat('OP')
            right = self.expr()
            return Assign(left, op, right)
        raise Exception("Invalid Syntax: expected =, got " + op.value)

    def variable(self):
        node = Var(self.token)
        self.eat('IDENT')
        return node


class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__    # visit_BinOp ~ visit_UnaryOp
        visitor = getattr(self, method_name, self.generic_visit)
        # print(method_name)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class Symbol:
    def __init__(self, name, category, type=None):
        self.name = name
        self.category = category
        self.type = type


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

    __repr__ = __str__


class VarSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)

    def __str__(self):
        return "<{class_name}(name='{name}', type='{type}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
            type=self.type,
        )

    __repr__ = __str__


class ProcedureSymbol(Symbol):
    def __init__(self, name, params=None):
        super(ProcedureSymbol, self).__init__(name)
        # a list of formal parameters
        self.params = params if params is not None else []

    def __str__(self):
        return '<{class_name}(name={name}, parameters={params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            params=self.params,
        )

    __repr__ = __str__


class ScopedSymbolTable(object):
    def __init__(self, scope_name, scope_level):
        self._symbols = OrderedDict()
        self.scope_name = scope_name
        self.scope_level = scope_level
        self._init_builtins()

    def _init_builtins(self):
        self.insert(BuiltinTypeSymbol('INTEGER'))
        self.insert(BuiltinTypeSymbol('REAL'))

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
        print('Lookup: %s' % name)
        symbol = self._symbols.get(name)
        # 'symbol' is either an instance of the Symbol class or None
        return symbol


class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        self.symtab = ScopedSymbolTable(scope_name='global', scope_level=1)
        self.current_scope = None

    def visit_Block(self, node):
        for declaration in node.declarations:
            self.visit(declaration)
        self.visit(node.compound_statement)

    def visit_Program(self, node):
        self.visit(node.block)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Num(self, node):
        pass

    def visit_UnaryOp(self, node):
        self.visit(node.expr)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_NoOp(self, node):
        pass

    def visit_VarDecl(self, node):
        type_name = node.type_node.value
        type_symbol = self.current_scope.lookup(type_name)

        # We have all the information we need to create a variable symbol.
        # Create the symbol and insert it into the symbol table.
        var_name = node.var_node.value
        var_symbol = VarSymbol(var_name, type_symbol)

        self.current_scope.insert(var_symbol)

    def visit_Assign(self, node):
        var_name = node.left.value
        var_symbol = self.symtab.lookup(var_name)
        if var_symbol is None:
            raise NameError(repr(var_name))

        self.visit(node.right)

    def visit_Var(self, node):
        var_name = node.value
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            raise Exception(
                "Error: Symbol(identifier) not found '%s'" % var_name
            )

    def visit_ProcedureDecl(self, node):
        proc_name = node.proc_name
        proc_symbol = ProcedureSymbol(proc_name)
        self.current_scope.insert(proc_symbol)

        print('ENTER scope: %s' % proc_name)
        # Scope for parameters and local variables
        procedure_scope = ScopedSymbolTable(
            scope_name=proc_name,
            scope_level=2,
        )
        self.current_scope = procedure_scope

        # Insert parameters into the procedure scope
        for param in node.params:
            param_type = self.current_scope.lookup(param.type_node.value)
            param_name = param.var_node.value
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
            proc_symbol.params.append(var_symbol)

        self.visit(node.block_node)

        print(procedure_scope)
        print('LEAVE scope: %s' % proc_name)

    def visit_Program(self, node):
        print('ENTER scope: global')
        global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
        )
        self.current_scope = global_scope

        # visit subtree
        self.visit(node.block)

        print(global_scope)
        print('LEAVE scope: global')


class Interpreter(NodeVisitor):
    def __init__(self, text):
        self.parser = Parser(text)
        self.GLOBAL_SCOPE = OrderedDict()

    def visit_BinOp(self, node):
        if node.op.value == '+':
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.value == '-':
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.value == '*':
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.value == '/':
            return self.visit(node.left) / self.visit(node.right)
        elif node.op.value == '//':
            return self.visit(node.left) // self.visit(node.right)
        # elif node.op.value == '**':
        #     return self.visit(node.left) ** self.visit(node.right)

    def visit_UnaryOp(self, node):
        op = node.op.value
        if op == '+':
            return +self.visit(node.expr)
        if op == '-':
            return -self.visit(node.expr)

    def visit_Num(self, node):
        return node.value

    def visit_String(self, node):
        return node.value

    def visit_Program(self, node):
        for statement in node.block:
            print(self.visit(statement))

    def visit_NoOp(self, node):     # dummy node
        return "End of the program"

    def visit_Assign(self, node):
        var_name = node.left.value
        self.GLOBAL_SCOPE[var_name] = self.visit(node.right)
        return "Assign {} with {}".format(var_name, self.GLOBAL_SCOPE[var_name])

    def visit_Var(self, node):
        var_name = node.value
        val = self.GLOBAL_SCOPE.get(var_name)
        if val is None:
            raise NameError(repr(var_name))
        else:
            return val

    def interpret(self):
        tree = self.parser.program()
        return self.visit(tree)


def main():
    with open("test.txt") as f:
        code = f.read()
        interpreter = Interpreter(code)
        interpreter.interpret()
    # while True:
    #     try:
    #         text = input('>>')
    #     except EOFError:
    #         break
    #     if not text:
    #         continue
    #     if text == 'q':
    #         break
    #     interpreter = Interpreter(text)
    #     result = interpreter.interpret()


if __name__ == '__main__':
    main()

