from enum import auto, IntEnum, unique


@unique
class TokenType(IntEnum):
    """Map token types in Lox to an integer for ease of use."""

    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()
    QMARK = auto()
    COLON = auto()

    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESSER = auto()
    LESSER_EQUAL = auto()

    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    AND = auto()
    BREAK = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FUN = auto()
    FOR = auto()
    IF = auto()
    NIL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()

    EOF = auto()


class Token:
    """Object to store relevant information for token together.

    Parameters
    ----------
    token_type : TokenType
        Enum that describes token
    lexeme : str
        Snippet of source that corresponds to scanned token
    literal : str | float
        Number or string or the like that corresponds to the lexeme
    line : int
        Line number of lexeme in source, used often in case of error
        reporting
    """
    def __init__(
        self,
        token_type: TokenType,
        lexeme: str,
        literal: str | float,
        line: int,
    ):
        self.token_type = token_type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __str__(self) -> str:
        if self.literal:
            return f"(LINE {self.line}, {self.token_type.name}) {self.lexeme} {self.literal}"
        return f"(LINE {self.line}, {self.token_type.name}) {self.lexeme}"

    def __repr__(self) -> str:
        if self.literal:
            return f"TOKEN {self.token_type.name} ({self.lexeme})"
        return f"TOKEN {self.token_type.name}"
