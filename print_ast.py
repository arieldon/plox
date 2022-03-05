import expr
from tokens import Token, TokenType


class ASTPrinter(expr.Visitor):
    def format(self, expression: expr.Expr) -> str:
        return expression.accept(self)

    def parenthesize(self, name: str, *expressions: expr.Expr) -> str:
        builder = []

        builder.append("(")
        builder.append(name)
        for expression in expressions:
            builder.append(" ")
            builder.append(expression.accept(self))
        builder.append(")")

        return "".join(builder)

    def visit_binary_expr(self, expression: expr.Binary) -> str:
        return self.parenthesize(expression.operator.lexeme, expression.left, expression.right)

    def visit_grouping_expr(self, expression: expr.Grouping) -> str:
        return self.parenthesize("group", expression.expression)

    def visit_literal_expr(self, expression: expr.Literal) -> str:
        if expression.value is None:
            return "nil"
        return str(expression.value)

    def visit_unary_expr(self, expression: expr.Unary) -> str:
        return self.parenthesize(expression.operator.lexeme, expression.right)


def main() -> None:
    expression = expr.Binary(
        expr.Unary(
            Token(TokenType.MINUS, "-", None, 1),
            expr.Literal(123),
        ),
        Token(TokenType.STAR, "*", None, 1),
        expr.Grouping(expr.Literal(45.67)),
    )

    print(ASTPrinter().format(expression))


if __name__ == "__main__":
    main()
