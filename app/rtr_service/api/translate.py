from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from ..auth.oauth import get_current_user
from ..llm.client import llm_client
from typing import Dict, Any

router = APIRouter()


class TranslateRequest(BaseModel):
    """Request model for natural language translation"""
    text: str
    target_format: str = "structured"  # or "ansible"


class TranslateResponse(BaseModel):
    """Response model for translation results"""
    original_text: str
    translated_action: Dict[str, Any]
    confidence: float
    suggestions: list = []


@router.post("/translate", response_model=TranslateResponse)
async def translate_natural_language(
    request: TranslateRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Translate natural language mitigation requests to structured actions
    
    This endpoint uses an LLM to convert human-readable mitigation requests
    into structured action formats that can be processed by the RTR system.
    """
    try:
        # Ensure LLM is loaded
        if not llm_client.is_loaded():
            try:
                llm_client.load_model()
            except FileNotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"LLM model not available: {str(e)}"
                )
        
        # Translate the input
        translation_result = llm_client.translate_to_action(request.text)
        
        return TranslateResponse(
            original_text=request.text,
            translated_action=translation_result.get("structured_format", {}),
            confidence=translation_result.get("confidence", 0.0),
            suggestions=translation_result.get("suggestions", [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )
