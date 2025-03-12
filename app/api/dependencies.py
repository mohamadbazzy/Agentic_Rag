from fastapi import Header, HTTPException
from typing import Optional

# This is a simple example - you could add API key validation,
# rate limiting, or other shared functionality

async def get_token_header(x_token: Optional[str] = Header(None)):
    """
    Example dependency for API key validation
    """
    if x_token is None:
        raise HTTPException(status_code=400, detail="X-Token header is missing")
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=401, detail="Invalid X-Token")
    return x_token
