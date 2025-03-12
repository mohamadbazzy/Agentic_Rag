from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from app.services.advisor import process_query

router = APIRouter()

@router.post("/query", response_model=Dict[str, str])
async def query_advisor(query: Dict[str, str]):
    """
    Process a student query through the academic advisor system
    """
    if "text" not in query:
        raise HTTPException(status_code=400, detail="Query text is required")
    
    result = process_query(query["text"])
    
    return {"response": result}
