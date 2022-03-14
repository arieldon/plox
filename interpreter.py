from typing import Any

import environment
import expr
import lox
import stmt
import tokens


class Interpreter(expr.Visitor, stmt.Visitor):
    def __init__(self) -> None:
        self.env = environment.Environment()

    def interpret(self, statements: list[stmt.Stmt]) -> None:
        try:
            for statement in statements:
                self.execute(statement)
        except RunningTimeError as error:
            lox.runtime_error(error)

    def evaluate(self, expression: expr.Expr) -> Any:
        return expression.accept(self)

    def execute(self, statement: stmt.Stmt) -> None:
        statement.accept(self)

    def execute_block(
        self, statements: list[None | stmt.Stmt], env: environment.Environment
    ) -> None:
        previous = self.env
        try:
            self.env = env
            for statement in statements:
                if statement:
                    self.execute(statement)
        finally:
            self.env = previous

    def visit_block_stmt(self, statement: stmt.Block) -> None:
        self.execute_block(statement.statements, environment.Environment(self.env))

    def visit_expression_stmt(self, statement: stmt.Expression) -> None:
        self.evaluate(statement.expression)

    def visit_if_stmt(self, statement: stmt.If) -> None:
        if self.is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.then_branch)
        elif statement.else_branch is not None:
            self.execute(statement.else_branch)

    def visit_print_stmt(self, statement: stmt.Print) -> None:
        value = self.evaluate(statement.expression)
        print(self.stringify(value))

    def visit_var_stmt(self, statement: stmt.Var) -> None:
        value = None
        if statement.initializer:
            value = self.evaluate(statement.initializer)
        self.env.define(statement.name.lexeme, value)

    def visit_assign_expr(self, expression: expr.Assign) -> object:
        value = self.evaluate(expression.value)
        self.env.assign(expression.name, value)
        return value

    def visit_binary_expr(self, expression: expr.Binary) -> None | str | float:
        left = self.evaluate(expression.left)
        right = self.evaluate(expression.right)

        match expression.operator.token_type:
            case tokens.TokenType.GREATER:
                self.check_number_operands(expression.operator, left, right)
                return float(left) > float(right)
            case tokens.TokenType.GREATER_EQUAL:
                self.check_number_operands(expression.operator, left, right)
                return float(left) >= float(right)
            case tokens.TokenType.LESSER:
                self.check_number_operands(expression.operator, left, right)
                return float(left) < float(right)
            case tokens.TokenType.LESSER_EQUAL:
                self.check_number_operands(expression.operator, left, right)
                return float(left) <= float(right)
            case tokens.TokenType.BANG_EQUAL:
                return not self.is_equal(left, right)
            case tokens.TokenType.EQUAL_EQUAL:
                return self.is_equal(left, right)
            case tokens.TokenType.MINUS:
                self.check_number_operands(expression.operator, left, right)
                return float(left) - float(right)
            case tokens.TokenType.SLASH:
                self.check_number_operands(expression.operator, left, right)
                return float(left) / float(right)
            case tokens.TokenType.STAR:
                self.check_number_operands(expression.operator, left, right)
                return float(left) * float(right)
            case tokens.TokenType.PLUS if isinstance(left, float) and isinstance(right, float):
                return float(left) + float(right)
            case tokens.TokenType.PLUS if isinstance(left, str) and isinstance(right, str):
                return str(left) + str(right)
            case tokens.TokenType.PLUS:
                # Catch any case for PLUS where operators are not either both
                # numbers or both strings.
                raise RunningTimeError(
                    expression.operator, "operands must be two numbers or two strings"
                )

        # Unreachable
        assert False, "This statement should not be reached."
        return None

    def visit_literal_expr(self, expression: expr.Literal) -> None | str | float:
        return expression.value

    def visit_logical_expr(self, expression: expr.Logical) -> object:
        left = self.evaluate(expression.left)
        if expression.operator.token_type == tokens.TokenType.OR:
            if self.is_truthy(left):
                return left
        else:
            if not self.is_truthy(left):
                return left
        return self.evaluate(expression.right)

    def visit_grouping_expr(self, expression: expr.Grouping) -> expr.Expr:
        return expression.expression

    def visit_unary_expr(self, expression: expr.Unary) -> float:
        right = self.evaluate(expression.right)

        match expression.operator.token_type:
            case tokens.TokenType.MINUS:
                self.check_number_operand(expression.operator, right)
                return -float(right)
            case tokens.TokenType.BANG:
                return not self.is_truthy(right)

        # Unreachable
        assert False, "This statement should not be reached."
        return None

    def visit_variable_expr(self, expression: expr.Variable) -> object:
        return self.env.get(expression.name)

    def check_number_operand(self, operator: tokens.Token, operand: object) -> None:
        if isinstance(operand, float):
            return
        raise RunningTimeError(operator, "operand must be a number")

    def check_number_operands(
        self, operator: tokens.Token, left: object, right: object
    ) -> None:
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RunningTimeError(operator, "operands must be a number")

    def is_truthy(self, item: object) -> bool:
        if not item:
            return False
        elif isinstance(item, bool):
            return bool(item)
        return True

    def is_equal(self, a: object, b: object) -> bool:
        if a is None and b is None:
            return True
        elif a is None:
            return False
        return a == b

    def stringify(self, item: object) -> str:
        if item is None:
            return "nil"

        if isinstance(item, float):
            text = str(item)
            if text.endswith(".0"):
                text = text[:len(text) - 2]
            return text

        return str(item)


class RunningTimeError(RuntimeError):
    def __init__(self, token: tokens.Token, message: str) -> None:
        self.token = token
        self.message = message

    def __str__(self) -> str:
        return f"{self.message}\n[line {self.token.line}]"
