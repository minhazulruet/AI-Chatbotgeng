"""
Math Solver API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import base64
import mimetypes
from typing import Optional

from app.services.mathsolver_service import MathSolverService

router = APIRouter(prefix="/api/mathsolver", tags=["mathsolver"])

mathsolver_service = MathSolverService()


class MathSolverRequest(BaseModel):
    """Request model for math solver"""
    image: str  # Base64 encoded image
    image_type: str  # MIME type (e.g., "image/png")
    text: Optional[str] = None  # Optional text description


class MathSolverResponse(BaseModel):
    """Response model for math solver"""
    solution: str
    error: Optional[str] = None


@router.post("/solve", response_model=MathSolverResponse)
async def solve_math_problem(request: MathSolverRequest):
    """
    Solve a math problem from an image
    
    - **image**: Base64 encoded image data
    - **image_type**: MIME type of the image
    - **text**: Optional text description or question
    """
    try:
        # Validate image
        if not request.image:
            raise HTTPException(status_code=400, detail="Image is required")

        # Call the service to solve the problem
        solution = await mathsolver_service.solve_problem(
            image_base64=request.image,
            image_type=request.image_type,
            text_description=request.text
        )

        return MathSolverResponse(solution=solution)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error solving math problem: {str(e)}")
