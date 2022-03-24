import lox
from tokens import Token, TokenType


class Scanner:
    keywords = {
        "and": TokenType.AND,
        "class": TokenType.CLASS,
        "else": TokenType.ELSE,
        "false": TokenType.FALSE,
        "for": TokenType.FOR,
        "fun": TokenType.FUN,
        "if": TokenType.IF,
        "nil": TokenType.NIL,
        "or": TokenType.OR,
        "print": TokenType.PRINT,
        "return": TokenType.RETURN,
        "super": TokenType.SUPER,
        "this": TokenType.THIS,
        "true": TokenType.TRUE,
        "var": TokenType.VAR,
        "while": TokenType.WHILE,
    }

    def __init__(self, source: str):
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> list[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def scan_token(self) -> None:
        c = self.advance()
        match c:
            case "(": self.add_token(TokenType.LEFT_PAREN)
            case ")": self.add_token(TokenType.RIGHT_PAREN)
            case "{": self.add_token(TokenType.LEFT_BRACE)
            case "}": self.add_token(TokenType.RIGHT_BRACE)
            case ",": self.add_token(TokenType.COMMA)
            case ".": self.add_token(TokenType.DOT)
            case "-": self.add_token(TokenType.MINUS)
            case "+": self.add_token(TokenType.PLUS)
            case ";": self.add_token(TokenType.SEMICOLON)
            case "*": self.add_token(TokenType.STAR)
            case "!":
                self.add_token(TokenType.BANG_EQUAL if self.match("=") else TokenType.BANG)
            case "=":
                self.add_token(TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL)
            case "<":
                self.add_token(TokenType.LESSER_EQUAL if self.match("=") else TokenType.LESSER)
            case ">":
                self.add_token(
                    TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER
                )
            case "/":
                if self.match("/"):
                    # Skip single-line comments.
                    while self.peek() != "\n" and not self.is_at_end():
                        self.advance()
                elif self.match("*"):
                    # Skip multi-line comments.
                    comment_start = self.line
                    delimiters = 1
                    while delimiters:
                        curr = self.peek()
                        next = self.peek_next()
                        if next == "\0":
                            lox.error(comment_start, "unterminated block comment")
                            break
                        elif curr == "/" and next == "*":
                            delimiters += 1
                        elif curr == "*" and next == "/":
                            delimiters -= 1
                        elif curr == "\n":
                            self.line += 1
                        self.advance()
                    self.advance()
                else:
                    self.add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                # Ignore whitespace.
                pass
            case "\n":
                self.line += 1
            case "\"":
                self.string()
            case _:
                if self.is_digit(c):
                    self.number()
                elif self.is_alpha(c):
                    self.identifier()
                else:
                    lox.error(self.line, "unexpected character")

    def identifier(self) -> None:
        while self.is_alphanumeric(self.peek()):
            self.advance()

        if value := Scanner.keywords.get(self.source[self.start:self.current]):
            self.add_token(value)
        else:
            self.add_token(TokenType.IDENTIFIER)

    def number(self) -> None:
        while self.is_digit(self.peek()):
            self.advance()

        if self.peek() == "." and self.is_digit(self.peek_next()):
            self.advance()
            while self.is_digit(self.peek()):
                self.advance()

        self.add_token(TokenType.NUMBER, float(self.source[self.start:self.current]))

    def string(self) -> None:
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\n":
                self.line += 1
            self.advance()

        if self.is_at_end():
            lox.error(self.line, "unterminated string")
            return

        self.advance()
        self.add_token(TokenType.STRING, self.source[self.start + 1:self.current - 1])

    def match(self, expected: str) -> bool:
        if self.is_at_end():
            return False
        elif self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def peek(self) -> str:
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def is_alpha(self, c: str) -> bool:
        assert len(c) == 1, "c must be a character."
        return (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") or (c == "_")

    def is_alphanumeric(self, c: str) -> bool:
        assert len(c) == 1, "c must be a character."
        return self.is_alpha(c) or self.is_digit(c)

    def is_digit(self, c: str) -> bool:
        assert len(c) == 1, "c must be a character."
        return (c >= "0") and (c <= "9")

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        return c

    def add_token(self, token_type: TokenType, literal: None | str | float = None) -> None:
        self.tokens.append(
            Token(token_type, self.source[self.start:self.current], literal, self.line)
        )
