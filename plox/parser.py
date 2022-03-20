from typing import NoReturn

import expr
import lox
import stmt
from tokens import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse(self) -> list[stmt.Stmt]:
        statements: list[stmt.Stmt] = []
        while not self.is_at_end():
            if statement := self.declaration():
                statements.append(statement)
        return statements

    def expression(self) -> expr.Expr:
        return self.assignment()

    def declaration(self) -> None | stmt.Stmt:
        try:
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            if self.match(TokenType.FUN):
                return self.function("function")
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except ParseError:
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
            methods.append(self.function("method"))

        self.consume(TokenType.RIGHT_BRACE, "expect '}' after class body")
        return stmt.Class(name, superclass, methods)

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

    def for_statement(self) -> stmt.Stmt:
        self.consume(TokenType.LEFT_PAREN, "expect '(' after 'while'")

        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "expect ';' after loop condition")

        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()
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
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "expect ';' after return value")
        return stmt.Return(keyword, value)

    def while_statement(self) -> stmt.Stmt:
        self.consume(TokenType.LEFT_PAREN, "expect '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "expect ')' after condition")
        body = self.statement()
        return stmt.While(condition, body)

    def var_declaration(self) -> stmt.Stmt:
        name = self.consume(TokenType.IDENTIFIER, "expect variable name")

        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "expect ';' after variable declaration")
        return stmt.Var(name, initializer)

    def expression_statement(self) -> stmt.Stmt:
        expression = self.expression()
        self.consume(TokenType.SEMICOLON, "expect ';' after value")
        return stmt.Expression(expression)

    def function(self, kind: str) -> stmt.Function:
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

    def block(self) -> list[None | stmt.Stmt]:
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "expect '}' after block")
        return statements

    def assignment(self) -> expr.Expr:
        expression = self.or_expr()
        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expression, expr.Variable):
                return expr.Assign(expression.name, value)
            elif isinstance(expression, expr.Get):
                return expr.Set(expression.item, expression.name, value)

            self.error(equals, "invalid assignment target")
        return expression

    def or_expr(self) -> expr.Expr:
        expression = self.and_expr()
        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_expr()
            expression = expr.Logical(expression, operator, right)
        return expression

    def and_expr(self) -> expr.Expr:
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


    def match(self, *token_types: TokenType) -> bool:
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        self.error(self.peek(), message)

    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().token_type == token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().token_type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def error(self, token: Token, message: str) -> NoReturn:
        lox.error(token, message)
        raise ParseError()

    def synchronize(self) -> None:
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



class ParseError(Exception):
    pass
