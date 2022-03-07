import expr
import lox
import tokens


class Interpreter(expr.Visitor):
    def interpret(self, expression: expr.Expr):
        try:
            value = self.evaluate(expression)
            print(self.stringify(value))
        except RuntimeError as error:
            lox.Lox.runtime_error(error)

    def evaluate(self, expression: expr.Expr):
        return expression.accept(self)

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
                raise RuntimeError(
                    expression.operator, "operands must be two numbers or two strings"
                )

        # Unreachable
        assert False, "This statement should not be reached."
        return None

    def visit_literal_expr(self, expression: expr.Literal) -> None | str | float:
        return expression.value

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

    def check_number_operand(self, operator: tokens.Token, operand: object) -> None:
        if isinstance(operand, float):
            return
        raise RuntimeError(operator, "operand must be a number")

    def check_number_operands(self, operator: tokens.Token, left: object, right: object):
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RuntimeError(operator, "operands must be a number")

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
