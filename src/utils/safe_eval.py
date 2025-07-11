import ast
from typing import Any, Dict, List

__all__ = ["safe_eval", "validate_expression"]


def _eval(node: ast.AST, records: List[Dict[str, Any]]) -> float:
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, records)
        right = _eval(node.right, records)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("division by zero")
            return left / right
        raise ValueError("Unsupported operator")
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return -_eval(node.operand, records)
        if isinstance(node.op, ast.UAdd):
            return +_eval(node.operand, records)
        raise ValueError("Unsupported unary operator")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Invalid function call")
        name = node.func.id
        if name not in {"sum", "len"} or len(node.args) != 1:
            raise ValueError("Invalid function")
        arg = node.args[0]
        if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
            raise ValueError("Invalid argument")
        field = arg.value
        if name == "sum":
            return sum(float(r.get(field, 0)) for r in records)
        else:
            return len(records)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Invalid constant")
    raise ValueError("Unsupported expression")


def safe_eval(expression: str, records: List[Dict[str, Any]] | None = None) -> float:
    """Evaluate a simple arithmetic expression on ``records`` safely."""
    records = records or []
    tree = ast.parse(expression, mode="eval")
    return _eval(tree.body, records)


def validate_expression(expression: str) -> None:
    """Validate expression raising ValueError if invalid."""
    safe_eval(expression, [])
