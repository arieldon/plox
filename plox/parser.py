from typing import NoReturn

import expr
import lox
import stmt
from tokens import Token, TokenType


class Parser:
    """A recursive descent parser for Lox.

    Generate an abstract syntax tree (AST) given a sequence of tokens.

    Attributes
    ----------
    tokens : list[Token]
        Sequence of tokens passed from Scanner
    current: int
        Index of current token being parsed in sequence of tokens

    Methods
    -------
    parse()
        Parse tokens to form a syntax tree.

    Notes
    -----
    The following Backus-Naur Form (BNF) diagrams describe the grammar
    of Lox. The rules are listed from lowest to highest precedence, and
    they're parsed top to bottom.

    A program in Lox consists of a sequence of declarations, where a
    declaration is a statement that may bind a new identifier.
    Statements that do not bind a new identifier produce side effects
    nonetheless. Statements consist of keywords and values, where values
    are produced by expressions, and expressions consists of keywords,
    operators, and lexemes. Lexemes are strings from the source.

    program -> declaration* EOF ;

    declaration -> class_declaration
                |  function_declaration
                |  var_declaration
                |  statement ;

    class_declaration    -> "class" IDENTIFIER ( "<" IDENTIFIER )?
                            "{" function* "}" ;
    function_declaration -> "fun" function ;
    var_declaration      -> "var" var ( "," var)* ";" ;

    statement -> expression_statement
              |  for_statement
              |  if_statement
              |  print_statement
              |  return_statement
              |  while_statement
              |  block ;

    expression_statement -> expression ";"? ;
    for_statement        -> "for" "("
                            ( var_declaration | expression_statement | ";" )
                            expression? ";"
                            expression? ")" statement ;
    if_statement         -> "if" "(" expression ")" statement
                            ( "else" statement )? ;
    print_statement      -> "print" expression ";" ;
    return_statement     -> "return" expression ";" ;
    while_statement      -> "while" "(" expression ")" statement ;
    block                -> "{" declaration "}" ;

    expression -> comma

    comma       -> conditional ( "," conditional )* ;
    conditional -> logical_or "?" expression ":" conditional ;
    assignment  -> ( call "." )? IDENTIFIER "=" assignment
                |  logical_or ;
    logical_or  -> logical_and ( "or" logical_and )* ;
    logical_and -> equality ( "and" equality )* ;
    equality    -> comparison ( ( "!=" | "==" ) comparison )* ;
    comparison  -> term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
    term        -> factor ( ( "/" | "*" ) unary )* ;
    factor      -> unary ( ( "/" | "*" ) unary )* ;
    unary       -> ( "!" | "-" ) unary | call ;
    call        -> primary ( "(" arguments? ")" | "." IDENTIFIER )* ;
    primary     -> "true" | "false" | "nil" | "this"
                |  NUMBER | STRING | IDENTIFIER | "(" expression ")"
                |  "super" "." IDENTIFIER ;

    Lexemes are defined in Scanner instead of Parser.

    NUMBER     -> DIGIT + ( "." DIGIT + )? ;
    STRING     -> "\"" <any char except "\"">* "\"" ;
    IDENTIFIER -> ALPHA ( ALPHA | DIGIT )* ;
    ALPHA      -> "a" ... "z" | "A" ... "Z" | "_" ;
    DIGIT      -> "0" ... "9" ;

    These last three rules are defined and used for convenience in these
    diagrams -- they are not methods in the class.

    function   -> IDENTIFIER "(" parameters? ")" block ;
    parameters -> IDENTIFIER ( "," IDENTIFIER )* ;
    arguments  -> expression ( "," expression )* ;
    var        -> IDENTIFIER ( "=" conditional )? ;
    """

    def __init__(self, tokens: list[Token]) -> None:
        """
        Parameters
        ----------
        tokens: list[Token]
            Sequence of tokens passed from scanner
        """
        self.tokens = tokens
        self.current = 0

    def parse(self) -> list[stmt.Stmt]:
        """Produce a sequence of statements to interpret.

        This method represents the "program" rule in the BNF diagrams above.

        Returns
        -------
        statements : list[stmt.Stmt]
            A sequence of statements parsed from `tokens`
        """
        statements: list[stmt.Stmt] = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return statements

    def declaration(self) -> stmt.Stmt:
        try:
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            if self.match(TokenType.FUN):
                return self.function_declaration("function")
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except LoxParserError:
            self.synchronize()
        return None

    def class_declaration(self) -> stmt.Stmt:
        name = self.consume(TokenType.IDENTIFIER, "expect class name")

        if self.match(TokenType.LESSER):
            self.consume(TokenType.IDENTIFIER, "expect superclass name")
            superclass = expr.Variable(self.previous())
        else:
            superclass = None

        self.consume(TokenType.LEFT_BRACE, "expect '{' before class body")

        methods: list[stmt.Function] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.function_declaration("method"))

        self.consume(TokenType.RIGHT_BRACE, "expect '}' after class body")
        return stmt.Class(name, superclass, methods)

    def function_declaration(self, kind: str) -> stmt.Function:
        name = self.consume(TokenType.IDENTIFIER, f"expect {kind} name.")
        self.consume(TokenType.LEFT_PAREN, f"expect '(' after {kind} name.")

        parameters: list[Token] = []
        if not self.check(TokenType.RIGHT_PAREN):
            parameters.append(self.consume(TokenType.IDENTIFIER, "expect parameter name"))
            while self.match(TokenType.COMMA):
                if len(parameters) >= 255:
                    self.error(self.peek(), "cannot exceed 255 parameters")
                parameters.append(self.consume(TokenType.IDENTIFIER, "expect parameter name"))
        self.consume(TokenType.RIGHT_PAREN, "expect ')' after parameters")

        self.consume(TokenType.LEFT_BRACE, f"expect '{{' before {kind} body")
        body = self.block()
        return stmt.Function(name, parameters, body)

    def var_declaration(self) -> stmt.Stmt:
        variables: dict[Token, expr.Expr] = {}

        while True:
            name = self.consume(TokenType.IDENTIFIER, "expect variable name")
            if self.match(TokenType.EQUAL):
                initializer = self.conditional()
            else:
                initializer = None

            if name.lexeme not in map(lambda name: name.lexeme, variables):
                variables[name] = initializer
            else:
                self.error(name, "reuse of same variable in declaration")

            if not self.match(TokenType.COMMA):
                break

        self.consume(TokenType.SEMICOLON, "expect ';' after variable declaration")
        return stmt.Var(variables)

    def statement(self) -> stmt.Stmt:
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.LEFT_BRACE):
            return stmt.Block(self.block())
        return self.expression_statement()

    def expression_statement(self) -> stmt.Stmt:
        expression = self.expression()
        # The semicolon is optional. Consume it if it exists, or simply continue.
        self.match(TokenType.SEMICOLON)
        return stmt.Expression(expression)

    def for_statement(self) -> stmt.Stmt:
        self.consume(TokenType.LEFT_PAREN, "expect '(' after 'while'")

        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        else:
            condition = None
        self.consume(TokenType.SEMICOLON, "expect ';' after loop condition")

        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()
        else:
            increment = None
        self.consume(TokenType.RIGHT_PAREN, "expect ')' after for clauses")

        body = self.statement()
        if increment:
            body = stmt.Block([body, stmt.Expression(increment)])

        if condition is None:
            condition = expr.Literal(True)
        body = stmt.While(condition, body)

        if initializer is not None:
            body = stmt.Block([initializer, body])

        return body

    def if_statement(self) -> stmt.Stmt:
        self.consume(TokenType.LEFT_PAREN, "expect '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "expect ')' after if condition")

        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()

        return stmt.If(condition, then_branch, else_branch)

    def print_statement(self) -> stmt.Stmt:
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "expect ';' after value")
        return stmt.Print(value)

    def return_statement(self) -> stmt.Stmt:
        keyword = self.previous()
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()
        else:
            value = None

        self.consume(TokenType.SEMICOLON, "expect ';' after return value")
        return stmt.Return(keyword, value)

    def while_statement(self) -> stmt.Stmt:
        self.consume(TokenType.LEFT_PAREN, "expect '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "expect ')' after condition")
        body = self.statement()
        return stmt.While(condition, body)

    def block(self) -> list[stmt.Stmt]:
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "expect '}' after block")
        return statements

    def expression(self) -> expr.Expr:
        return self.comma()

    def comma(self) -> expr.Expr:
        expression = self.conditional()
        while self.match(TokenType.COMMA):
            right = self.conditional()
            expression = expr.Comma(expression, right)
        return expression

    def conditional(self) -> expr.Expr:
        expression = self.logical_or()
        if self.match(TokenType.QMARK):
            then_expression = self.expression()
            self.consume(TokenType.COLON, "expect ':' after first expression")
            else_expression = self.conditional()
            expression = expr.Conditional(expression, then_expression, else_expression)
        return expression

    def assignment(self) -> expr.Expr:
        expression = self.logical_or()
        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expression, expr.Variable):
                return expr.Assign(expression.name, value)
            elif isinstance(expression, expr.Get):
                return expr.Set(expression.item, expression.name, value)

            self.error(equals, "invalid assignment target")
        return expression

    def logical_or(self) -> expr.Expr:
        expression = self.logical_and()
        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.logical_and()
            expression = expr.Logical(expression, operator, right)
        return expression

    def logical_and(self) -> expr.Expr:
        expression = self.equality()
        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expression = expr.Logical(expression, operator, right)
        return expression

    def equality(self) -> expr.Expr:
        expression = self.comparison()
        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expression = expr.Binary(expression, operator, right)
        return expression

    def comparison(self) -> expr.Expr:
        expression = self.term()
        while self.match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESSER,
            TokenType.LESSER_EQUAL,
        ):
            operator = self.previous()
            right = self.term()
            expression = expr.Binary(expression, operator, right)
        return expression

    def term(self) -> expr.Expr:
        expression = self.factor()
        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expression = expr.Binary(expression, operator, right)
        return expression

    def factor(self) -> expr.Expr:
        expression = self.unary()
        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expression = expr.Binary(expression, operator, right)
        return expression

    def unary(self) -> expr.Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return expr.Unary(operator, right)
        return self.call()

    def finish_call(self, callee: expr.Expr) -> expr.Expr:
        arguments = []
        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.expression())
            while self.match(TokenType.COMMA):
                if len(arguments) >= 255:
                    self.error(self.peek(), "cannot exceed 255 arguments")
                arguments.append(self.expression())

        paren = self.consume(TokenType.RIGHT_PAREN, "expect ')' after arguments")
        return expr.Call(callee, paren, arguments)

    def call(self) -> expr.Expr:
        expression = self.primary()
        while True:
            if self.match(TokenType.LEFT_PAREN):
                expression = self.finish_call(expression)
            if self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "expect poerty name after '.'")
                expression = expr.Get(expression, name)
            else:
                break
        return expression

    def primary(self) -> expr.Expr:
        if self.match(TokenType.FALSE):
            return expr.Literal(False)
        elif self.match(TokenType.TRUE):
            return expr.Literal(True)
        elif self.match(TokenType.NIL):
            return expr.Literal(None)

        if self.match(TokenType.NUMBER, TokenType.STRING):
            return expr.Literal(self.previous().literal)

        if self.match(TokenType.SUPER):
            keyword = self.previous()
            self.consume(TokenType.DOT, "expect '.' after 'super'");
            method = self.consume(TokenType.IDENTIFIER, "expect superclass method name")
            return expr.Super(keyword, method)

        if self.match(TokenType.THIS):
            return expr.This(self.previous())

        if self.match(TokenType.IDENTIFIER):
            return expr.Variable(self.previous())

        if self.match(TokenType.LEFT_PAREN):
            expression = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return expr.Grouping(expression)

        self.error(self.peek(), "expected expression")
        return None


    def match(self, *token_types: TokenType) -> bool:
        """Consume next token if it matches at least one given type."""
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        """Register a token as parsed and progress to the next."""
        if self.check(token_type):
            return self.advance()
        self.error(self.peek(), message)

    def check(self, token_type: TokenType) -> bool:
        """Check that token matches given type without consuming it."""
        if self.is_at_end():
            return False
        return self.peek().token_type == token_type

    def advance(self) -> Token:
        """Consume current token and progress to the next."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        """Confirm all tokens have been parsed."""
        return self.peek().token_type == TokenType.EOF

    def peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Return the previous token consumed."""
        return self.tokens[self.current - 1]

    def error(self, token: Token, message: str) -> NoReturn:
        """Raise exception to create a point from which to synchronize.

        First output an error message. Then, raise an exception when the
        parser stumbles across a syntax error to unwind the stack. At
        some point along the unwind, in this case in method
        declaration(), use the exception as a means to recover the state
        of the parser and minimize cascaded errors.
        """
        lox.error(token, message)
        raise LoxParserError()

    def synchronize(self) -> None:
        """Recover the state of the parser after a syntax error.

        If a statement contains a syntax error, skip it. To restore the
        state of the parser, reduce cascading errors, and avoid a crash,
        find the beginning of the next statement and continue.
        """
        self.advance()
        while not self.is_at_end():
            if self.previous().token_type == TokenType.SEMICOLON:
                return

            match self.peek().token_type:
                case (
                    TokenType.CLASS |
                    TokenType.FOR |
                    TokenType.FUN |
                    TokenType.IF |
                    TokenType.PRINT |
                    TokenType.RETURN |
                    TokenType.VAR |
                    TokenType.WHILE
                ):
                    return

            self.advance()


class LoxParserError(Exception):
    """An empty exception to trigger synchronization upon error."""
    pass
