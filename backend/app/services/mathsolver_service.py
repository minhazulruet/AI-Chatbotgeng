"""
Math Solver Service - Handles AI-powered math problem solving
"""

import httpx
import os
import base64
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MathSolverService:
    """Service for solving math problems using OpenRouter API with Gemini 2.5 Flash"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-2.5-flash"
        # Get APP_URL from environment, or construct from environment PORT
        self.app_url = os.getenv("APP_URL") or f"http://localhost:{os.getenv('PORT', 10000)}"
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set, math solver may not work")

    async def solve_problem(
        self,
        image_base64: str,
        image_type: str,
        text_description: Optional[str] = None
    ) -> str:
        """
        Solve a math problem from an image using OpenRouter API
        
        Args:
            image_base64: Base64 encoded image
            image_type: MIME type of the image (e.g., "image/png")
            text_description: Optional text description or question
            
        Returns:
            Solution text from the AI model
        """
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")

        # Extract the actual base64 data if it includes the data URI prefix
        if image_base64.startswith("data:"):
            image_base64 = image_base64.split(",", 1)[1]

        # System prompt for concise but complete solutions
        system_prompt = """You are an expert math tutor solving mathematical problems.
Provide COMPLETE, step-by-step solutions with CONCISE explanations:
1. Identify the problem type
2. List key formulas needed
3. Solve step-by-step (show all calculations, don't skip steps)
4. State the final answer clearly
5. Include verification if applicable

Be concise in wording but COMPLETE in solution steps. Avoid verbose explanations.
Always show the full calculation without truncation.
Format step-by-step solutions clearly with proper mathematical notation."""

        # Build the user message
        user_text = text_description or "Please solve this math problem step by step."

        # Prepare the message content
        content = [
            {
                "type": "text",
                "text": user_text
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_type};base64,{image_base64}"
                }
            }
        ]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": self.app_url,
                        "X-OpenRouter-Title": "Khandakar's Digital Assistance",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": content
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2500,
                    }
                )

                response.raise_for_status()
                result = response.json()

                # Extract the solution from the response
                if "choices" in result and len(result["choices"]) > 0:
                    solution = result["choices"][0]["message"]["content"]
                    return solution
                else:
                    raise ValueError("Invalid response from OpenRouter API")

        except httpx.HTTPError as e:
            logger.error(f"OpenRouter API error: {str(e)}")
            raise ValueError(f"Failed to get solution from AI model: {str(e)}")
        except Exception as e:
            logger.error(f"Error in solve_problem: {str(e)}")
            raise ValueError(f"Error solving the problem: {str(e)}")
