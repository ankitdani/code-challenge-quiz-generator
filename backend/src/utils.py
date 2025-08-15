from fastapi import HTTPException
from clerk_backend_api import Clerk, AuthenticateRequestOptions
from dotenv import load_dotenv

import os
load_dotenv()

clerk_sdk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

def authenticate_get_user_request (request):
    try:
        request_state = clerk_sdk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authourized_parties=["http://localhost:5173", "http://localhost:5173"],
                jwt_key=os.getenv("JWT_KEY")
            )
        )
        
        if not request_state.is_signed_in:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = request_state.payload.get("sub")

        return {"user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))