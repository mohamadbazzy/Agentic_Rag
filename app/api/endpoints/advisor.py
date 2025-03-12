from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.advisor import process_query

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_advisor(query: QueryRequest):
    """
    Process a student query through the academic advisor system
    """
    try:
        result = process_query(query.text)
        
        # Return the result directly - don't nest it under 'response'
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
