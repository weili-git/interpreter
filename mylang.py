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

        raise Exception("Invalid Token")


class Parser:
    def __init__(self, text):
        self.lex = Lexer(text)
        self.token = self.lex.next_token()

    def eat(self, token_type):  # check type and advance
        print(self.token)
        if self.token.type == token_type:
            self.token = self.lex.next_token()
        else:
            raise Exception("Invalid Syntax: expected %s, got %s" % (token_type, self.token.type))

    def term(self):
        result = self.factor()
        while self.token.value in ['*', '/']:
            op = self.operator()
            if op == '*':
                result *= self.factor()
            if op == '/':
                result /= self.factor()
        return result

    def factor(self):
        token = self.token
        self.eat('INT')
        return token.value

    def operator(self):
        token = self.token
        self.eat('OP')
        return token.value

    def expr(self):
        result = self.term()
        while self.token.value in ['+', '-']:
            op = self.operator()
            if op == '+':
                result += self.term()
            if op == '-':
                result -= self.term()
        self.eat('EOF')
        return result


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
        interpreter = Parser(text)
        result = interpreter.expr()
        print(result)


if __name__ == '__main__':
    main()

