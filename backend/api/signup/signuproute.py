from fastapi import APIRouter, Request, Body, HTTPException
from pydantic import BaseModel
from db.auth import firebase_auth, db, requires_auth
from flask import jsonify 

router=APIRouter

@router.post("/signup")
@requires_auth
async def signup(request: Request):
    try:
        body = await request.json()
        token = body.get("token")

        if not token:
            raise HTTPException(status_code=400, detail="Missing token")

        # Verify the ID token
        decoded_token = firebase_auth.verify_id_token(token)
        uid = decoded_token["uid"]
        data = decoded_token.get("user_id")
        doc_ref = db.collection("AI_Interview").document("Interview").collection("USER").add(data)
        print("Document written to AI_Interview/USER with ID:", doc_ref[1].id)
        # Here you could store the user in Firestore or elsewhere
        return {"message": "Signup successful", "uid": uid, "data": data}

    except firebase_auth.InvalidIdTokenError:
        # raise HTTPException(status_code=401, detail="Invalid token")
        return jsonify({"error": "Invalid token"}), 401
    except firebase_auth.ExpiredIdTokenError:
        # raise HTTPException(status_code=401, detail="Token expired")
        return jsonify({"error": "Token expired"}), 401
    except Exception as e:
        # raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500