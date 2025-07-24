import jwt
import requests
from django.conf import settings

class ClerkUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwks = None

    def __call__(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            try:
                # Load Clerk JWKS (public keys)
                if not self.jwks:
                    jwks_url = settings.CLERK_JWKS_URL
                    self.jwks = requests.get(jwks_url).json()
                
                # Decode token
                unverified_header = jwt.get_unverified_header(token)
                kid = unverified_header["kid"]

                key = next(
                    (k for k in self.jwks["keys"] if k["kid"] == kid), None
                )
                if key:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    payload = jwt.decode(token, public_key, algorithms=["RS256"], audience=None)
                    request.clerk_user_id = payload.get("sub")
            except Exception as e:
                print(f"❌ Clerk token decode error: {e}")

        # Fallback for guests (query param)
        if not hasattr(request, "clerk_user_id"):
            guest_id = request.GET.get("clerk_user_id")
            if guest_id:
                request.clerk_user_id = guest_id

        return self.get_response(request)