from django.shortcuts import render
from django.http import JsonResponse
from .supabase import supabase
import json
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
# def inputProfileInfo(request):

@csrf_exempt
def fetchUserInfo(request):
    if request.method == 'POST':
        try:
            # Parse incoming request data
            data = json.loads(request.body)
            user_id = data.get("uuid")

            if not user_id:
                return JsonResponse({"error": "uuid is required"}, status=400)

            # Fetch user information from users table
            user_response = supabase.table("users") \
                .select("uuid, first_name, last_name, age, role, institution_id, graduation_year") \
                .eq("uuid", user_id) \
                .execute()

            # Fetch profile information from profiles table
            profile_response = supabase.table("profiles") \
                .select("bio, skills, linkedin_url, location, profile_photo, degree") \
                .eq("uuid", user_id) \
                .execute()

            # Check if user exists
            if not user_response.data:
                return JsonResponse({"error": "User not found"}, status=404)

            # Check if profile exists (optional)
            profile_data = profile_response.data[0] if profile_response.data else {}

            # Merge user and profile data
            user_info = {**user_response.data[0], **profile_data}

            return JsonResponse({"user_info": user_info}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
