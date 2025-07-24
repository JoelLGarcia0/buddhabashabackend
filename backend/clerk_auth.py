# clerk_auth.py
import requests
import jwt
from jwt import PyJWKClient
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import os
from django.contrib.auth import get_user_model

# Get the Clerk JWKS URL from environment or use a placeholder
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "https://clerk.dev/.well-known/jwks.json")

User = get_user_model()

class ClerkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        print(f"Auth header received: {auth_header[:50]}...")  # Debug log
        
        if not auth_header.startswith("Bearer "):
            print("No Bearer token found in Authorization header")  # Debug log
            return None

        token = auth_header.split(" ")[1]
        print(f"Token received: {token[:20]}...")  # Debug log

        try:
            print(f"Using JWKS URL: {CLERK_JWKS_URL}")  # Debug log
            jwks_client = PyJWKClient(CLERK_JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(token, signing_key.key, algorithms=["RS256"])
            request.clerk_user_id = decoded["sub"]  # Store Clerk user ID
            
            # ✅ Auto-create a Django user from Clerk info
            user, _ = User.objects.get_or_create(
                username=decoded["sub"],
                defaults={
                    "email": decoded.get("email", f"{decoded['sub']}@clerk.dev"),
                },
            ) # Debug log
            return (user, None)
        except Exception as e:
            print(f"Authentication failed: {str(e)}")  # Debug log
            raise AuthenticationFailed(f"Invalid Clerk token: {str(e)}")
