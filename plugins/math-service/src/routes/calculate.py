"""
Mathematical calculation routes.
"""
import ast
import operator
import math
from typing import Dict, Any, Optional, Union
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sympy import sympify, symbols, N
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication

from src.config import settings

router = APIRouter()

# Safe operators for expression evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe math functions
SAFE_FUNCTIONS = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'pow': pow,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
    'log': math.log,
    'log10': math.log10,
    'log2': math.log2,
    'exp': math.exp,
    'floor': math.floor,
    'ceil': math.ceil,
    'factorial': math.factorial,
    'gcd': math.gcd,
    'pi': math.pi,
    'e': math.e,
}


class CalculateRequest(BaseModel):
    """Request model for expression calculation."""
    expression: str = Field(..., description="Mathematical expression to evaluate")
    variables: Optional[Dict[str, Union[int, float]]] = Field(
        default=None, 
        description="Variables to substitute in the expression"
    )
    precision: int = Field(default=10, ge=1, le=15, description="Decimal precision for result")
    use_symbolic: bool = Field(default=False, description="Use symbolic computation (SymPy)")


class CalculateResponse(BaseModel):
    """Response model for calculation."""
    success: bool
    data: Dict[str, Any]
    request_id: Optional[str] = None
    timestamp: str


def safe_eval(expression: str, variables: Optional[Dict[str, float]] = None) -> float:
    """
    Safely evaluate a mathematical expression.
    
    Uses AST parsing to ensure only safe operations are performed.
    """
    # Replace common math constants
    expression = expression.replace('pi', str(math.pi))
    expression = expression.replace('e', str(math.e))
    
    # Substitute variables
    if variables:
        for var, value in variables.items():
            expression = expression.replace(var, str(value))
    
    try:
        tree = ast.parse(expression, mode='eval')
        return _eval_node(tree.body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")


def _eval_node(node: ast.AST) -> float:
    """Recursively evaluate an AST node."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Invalid constant: {node.value}")
    
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return SAFE_OPERATORS[op_type](left, right)
    
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        operand = _eval_node(node.operand)
        return SAFE_OPERATORS[op_type](operand)
    
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in SAFE_FUNCTIONS:
                args = [_eval_node(arg) for arg in node.args]
                return SAFE_FUNCTIONS[func_name](*args)
        raise ValueError(f"Unsupported function call")
    
    elif isinstance(node, ast.Name):
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unknown variable: {node.id}")
    
    raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def symbolic_eval(expression: str, variables: Optional[Dict[str, float]] = None, precision: int = 10) -> str:
    """Evaluate expression using SymPy for symbolic computation."""
    try:
        # Parse the expression
        expr = sympify(expression)
        
        # Substitute variables if provided
        if variables:
            symbol_dict = {symbols(k): v for k, v in variables.items()}
            expr = expr.subs(symbol_dict)
        
        # Evaluate numerically
        result = N(expr, precision)
        return str(result)
    except Exception as e:
        raise ValueError(f"Symbolic evaluation failed: {str(e)}")


@router.post("/calculate")
async def calculate(request: Request, body: CalculateRequest):
    """
    Evaluate a mathematical expression.
    
    Supports basic arithmetic, trigonometric functions, logarithms, and variable substitution.
    """
    from datetime import datetime
    
    try:
        if body.use_symbolic:
            result = symbolic_eval(body.expression, body.variables, body.precision)
            # Try to convert to float for numeric results
            try:
                result = float(result)
                result = round(result, body.precision)
            except (ValueError, TypeError):
                pass  # Keep as string for symbolic results
        else:
            result = safe_eval(body.expression, body.variables)
            result = round(result, body.precision)
        
        return CalculateResponse(
            success=True,
            data={
                "result": result,
                "expression": body.expression,
                "variables": body.variables,
                "precision": body.precision,
            },
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        return CalculateResponse(
            success=False,
            data={
                "error": str(e),
                "expression": body.expression,
            },
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
