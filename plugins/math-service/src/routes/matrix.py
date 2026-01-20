"""
Matrix operation routes.
"""
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime

router = APIRouter()


class MatrixRequest(BaseModel):
    """Request model for matrix operations."""
    operation: str = Field(..., description="Matrix operation to perform")
    matrixA: List[List[float]] = Field(..., description="First matrix")
    matrixB: Optional[List[List[float]]] = Field(None, description="Second matrix (for binary operations)")
    scalar: Optional[float] = Field(None, description="Scalar value (for scalar operations)")


class MatrixResponse(BaseModel):
    """Response model for matrix operations."""
    success: bool
    data: Dict[str, Any]
    request_id: Optional[str] = None
    timestamp: str


def validate_matrix(matrix: List[List[float]], name: str = "matrix") -> np.ndarray:
    """Validate and convert a matrix to numpy array."""
    arr = np.array(matrix)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 2-dimensional")
    if arr.shape[0] > 1000 or arr.shape[1] > 1000:
        raise ValueError(f"{name} exceeds maximum size of 1000x1000")
    return arr


@router.post("/matrix")
async def matrix_operation(request: Request, body: MatrixRequest):
    """
    Perform matrix operations.
    
    Supported operations:
    - add: Add two matrices
    - subtract: Subtract matrix B from matrix A
    - multiply: Matrix multiplication (A × B)
    - elementwise_multiply: Element-wise multiplication
    - transpose: Transpose matrix A
    - inverse: Inverse of matrix A
    - determinant: Determinant of matrix A
    - trace: Trace of matrix A
    - eigenvalues: Eigenvalues of matrix A
    - rank: Rank of matrix A
    - scalar_multiply: Multiply matrix by scalar
    """
    try:
        A = validate_matrix(body.matrixA, "matrixA")
        result: Union[np.ndarray, float]
        
        op = body.operation.lower()
        
        # Unary operations (only need matrix A)
        if op == "transpose":
            result = A.T
        
        elif op == "inverse":
            if A.shape[0] != A.shape[1]:
                raise ValueError("Matrix must be square for inverse")
            result = np.linalg.inv(A)
        
        elif op == "determinant":
            if A.shape[0] != A.shape[1]:
                raise ValueError("Matrix must be square for determinant")
            result = float(np.linalg.det(A))
        
        elif op == "trace":
            result = float(np.trace(A))
        
        elif op == "eigenvalues":
            if A.shape[0] != A.shape[1]:
                raise ValueError("Matrix must be square for eigenvalues")
            eigenvalues = np.linalg.eigvals(A)
            # Convert to real if all imaginary parts are ~0
            if np.allclose(eigenvalues.imag, 0):
                eigenvalues = eigenvalues.real
            result_list = eigenvalues.tolist()
            return MatrixResponse(
                success=True,
                data={
                    "eigenvalues": result_list,
                    "operation": op,
                },
                request_id=getattr(request.state, 'request_id', None),
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
        
        elif op == "rank":
            result = int(np.linalg.matrix_rank(A))
        
        elif op == "norm":
            result = float(np.linalg.norm(A))
        
        elif op == "scalar_multiply":
            if body.scalar is None:
                raise ValueError("Scalar value required for scalar_multiply")
            result = A * body.scalar
        
        # Binary operations (need matrix A and B)
        elif op in ["add", "subtract", "multiply", "elementwise_multiply"]:
            if body.matrixB is None:
                raise ValueError(f"matrixB required for {op} operation")
            B = validate_matrix(body.matrixB, "matrixB")
            
            if op == "add":
                if A.shape != B.shape:
                    raise ValueError("Matrices must have the same dimensions for addition")
                result = A + B
            
            elif op == "subtract":
                if A.shape != B.shape:
                    raise ValueError("Matrices must have the same dimensions for subtraction")
                result = A - B
            
            elif op == "multiply":
                if A.shape[1] != B.shape[0]:
                    raise ValueError(f"Cannot multiply matrices: {A.shape} × {B.shape}")
                result = np.matmul(A, B)
            
            elif op == "elementwise_multiply":
                if A.shape != B.shape:
                    raise ValueError("Matrices must have the same dimensions for element-wise multiplication")
                result = A * B
        
        else:
            raise ValueError(f"Unknown operation: {op}")
        
        # Format result
        if isinstance(result, np.ndarray):
            result_data = {
                "result": result.tolist(),
                "shape": list(result.shape),
                "operation": op,
            }
        else:
            result_data = {
                "result": result,
                "operation": op,
            }
        
        return MatrixResponse(
            success=True,
            data=result_data,
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    
    except Exception as e:
        return MatrixResponse(
            success=False,
            data={"error": str(e)},
            request_id=getattr(request.state, 'request_id', None),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )


@router.get("/matrix/operations")
async def list_matrix_operations():
    """List all supported matrix operations."""
    return {
        "success": True,
        "data": {
            "unary_operations": [
                "transpose", "inverse", "determinant", "trace", 
                "eigenvalues", "rank", "norm", "scalar_multiply"
            ],
            "binary_operations": [
                "add", "subtract", "multiply", "elementwise_multiply"
            ],
        },
    }
