

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
        self.ch = self.text[self.pos]
        self.ln = 1     # line number
        self.col = 1    # column
        self.keywords = ['def', 'return', 'end', 'if', 'then', 'elif', 'else', 'true', 'false']
        self.operators = ['+', '-', '*', '/', '//', '**', '=', '==', ';', ':', '||', '&&', '!']

    def advance(self):
        if self.ch == '\n':
            self.ln += 1
            self.col = 0
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.ch = None  # Indicates end of input
        else:
            self.ch = self.text[self.pos]
            self.col += 1

    def skip_whitespace(self):
        while self.pos < len(self.text) and self.ch.isspace():
            if self.ch == '\n':
                return
            self.advance()

    def skip_comment(self):
        if self.ch == '#':
            while self.pos < len(self.text) and self.ch != '\n':    # '\n' 作为token，不需要跳过
                self.advance()

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos > len(self.text) - 1:
            return None
        else:
            return self.text[peek_pos]

    def peek_token(self):
        pos = self.pos
        ch = self.ch
        token = self.next_token()
        self.pos = pos
        self.ch = ch
        return token

    def identifier(self):
        result = ''
        while self.pos < len(self.text) and self.ch.isalnum():
            result += self.ch
            self.advance()
        if result in self.keywords:
            if result in ['true', 'false']:
                return Token('BOOL', result == 'true')
            return Token(result.upper(), None)
        return Token('IDENT', result)

    def number(self):
        result = ''
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
        ln_ = self.ln
        col_ = self.col
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
            raise Exception("LexerError: EOF while scanning the string literal, line:{} col:{}".format(ln_, col_))
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

        if self.ch == '(':
            self.advance()
            return Token('(', None)

        if self.ch == ')':
            self.advance()
            return Token(')', None)

        if self.ch == ',':
            self.advance()
            return Token(',', None)

        if self.ch == '\n':
            self.advance()
            return Token('NEWLINE', '\n')

        raise Exception('LexerError: unexpected token on line:{} col:{}'.format(self.ln, self.col))


# lex = Lexer('1+$"+1"\n2+2')
# token = lex.next_token()
# while token.type != 'EOF':
#     print(token)
#     token = lex.next_token()

