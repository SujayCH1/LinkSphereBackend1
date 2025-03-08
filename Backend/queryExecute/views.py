from django.shortcuts import render
from django.http import JsonResponse
from .supabase import supabase
import json
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def institution_list(request):
    if request.method == 'GET':
        try:
            # Fetch all institution names
            response = supabase.table("institutions").select("name").execute()

            if not response.data:
                return JsonResponse({"error": "No institutions found"}, status=404)

            # Extract names and return as list
            institution_names = [inst["name"] for inst in response.data]
            return JsonResponse({"institutions": institution_names}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def upsert_user(request):
    if request.method == 'POST':
        try:
            # Parse request body
            data = json.loads(request.body)

            user_id = data.get("uuid")
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            date_of_birth = data.get("date_of_birth")  # Changed from age to date_of_birth
            role = data.get("role")
            institution_name = data.get("institution_name")  # Institution name instead of ID
            graduation_year = data.get("graduation_year")
            is_premium = str(data.get("is_premium", "false")).lower() == "true"  # Convert to boolean
            
            # Profile fields
            bio = data.get("bio", "")
            skills = data.get("skills", [])
            linkedin_url = data.get("linkedin_url", "")
            location = data.get("location", "")
            degree = data.get("degree", "")

            if not user_id or not institution_name:
                return JsonResponse({"error": "uuid and institution_name are required"}, status=400)

            # Find institution ID based on institution name
            institution_response = supabase.table("institutions") \
                .select("institution_id") \
                .eq("name", institution_name) \
                .single() \
                .execute()

            if not institution_response.data:
                return JsonResponse({"error": "Institution not found"}, status=404)

            institution_id = institution_response.data["institution_id"]

            # Construct user data dictionary
            user_data = {
                "uuid": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": date_of_birth,  # Changed from age
                "role": role,
                "institution_id": institution_id,  # Now using institution_id instead of name
                "graduation_year": int(graduation_year) if graduation_year else None,
                "is_premium": is_premium
            }

            # Construct profile data dictionary (excluding profile photo)
            profile_data = {
                "uuid": user_id,
                "bio": bio,
                "skills": skills if isinstance(skills, list) else [skills],  # Ensure list format
                "linkedin_url": linkedin_url,
                "location": location,
                "degree": degree
            }

            # Check if user already exists
            existing_user = supabase.table("users").select("uuid").eq("uuid", user_id).execute()

            if existing_user.data:
                # User exists, update record
                supabase.table("users").update(user_data).eq("uuid", user_id).execute()
            else:
                # User does not exist, insert new record
                supabase.table("users").insert([user_data]).execute()

            # Check if profile already exists
            existing_profile = supabase.table("profiles").select("uuid").eq("uuid", user_id).execute()

            if existing_profile.data:
                # Profile exists, update record
                supabase.table("profiles").update(profile_data).eq("uuid", user_id).execute()
            else:
                # Profile does not exist, insert new record
                supabase.table("profiles").insert([profile_data]).execute()

            return JsonResponse({"message": "User and profile upserted successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def fetchUserInfo(request):
    if request.method == 'GET':
        try:
            user_id = request.GET.get("uuid")

            if not user_id:
                return JsonResponse({"error": "uuid is required"}, status=400)

            user_response = supabase.table("users") \
                .select("uuid, first_name, last_name, age, role, institution_id, graduation_year") \
                .eq("uuid", user_id) \
                .execute()

            profile_response = supabase.table("profiles") \
                .select("bio, skills, linkedin_url, location, profile_photo, degree") \
                .eq("uuid", user_id) \
                .execute()

            if not user_response.data:
                return JsonResponse({"error": "User not found"}, status=404)

            profile_data = profile_response.data[0] if profile_response.data else {}
            user_info = {**user_response.data[0], **profile_data}

            return JsonResponse({"user_info": user_info}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
