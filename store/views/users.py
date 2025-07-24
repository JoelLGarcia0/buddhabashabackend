from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from store.models import UserProfile
from store.serializers import UserProfileSerializer



class UserProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, clerk_user_id):
        try:
            profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
            serializer = UserProfileSerializer(profile)
            print(f"Retrieved profile for {clerk_user_id}:", serializer.data)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            print(f"No profile found for {clerk_user_id}")
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        print("Incoming POST to /api/user-profile/", request.data)
        clerk_user_id = request.data.get("clerk_user_id")
        if not clerk_user_id:
            return Response({"error": "Missing clerk_user_id"}, status=400)

        profile, created = UserProfile.objects.get_or_create(clerk_user_id=clerk_user_id)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            print("Profile saved/updated:", serializer.data)
            return Response(serializer.data, status=201 if created else 200)
        else:
            print("Invalid data:", serializer.errors)
            return Response(serializer.errors, status=400)
