from django.http import JsonResponse
from .supabase import supabase
import pandas as pd
import numpy as np
from django.views.decorators.csrf import csrf_exempt
from sentence_transformers import SentenceTransformer
import os

# Load pre-trained model for semantic embeddings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "sentence_transformer")
model = SentenceTransformer(MODEL_PATH)

@csrf_exempt
def smartConnectAlgorithm(request):
    if request.method == 'GET':
        try:
            # Get query parameters
            user_id = request.GET.get("uuid")
            user_type = request.GET.get("user_type")

            if not user_id or not user_type:
                return JsonResponse({"error": "uuid and user_type are required"}, status=400)

            # Fetch institution name for the given user
            user_info = supabase.table("users").select("institution_id").eq("uuid", user_id).execute()
            if not user_info.data or "institution_id" not in user_info.data[0]:
                return JsonResponse({"error": "User institution not found"}, status=404)

            institution_id = user_info.data[0]["institution_id"]

            # Fetch user profile to get their skills
            user_profile = supabase.table("profiles").select("skills").eq("uuid", user_id).execute()
            if not user_profile.data or "skills" not in user_profile.data[0]:
                return JsonResponse({"error": "User skills not found"}, status=404)

            user_skills = ", ".join(user_profile.data[0]["skills"])
            user_vector = model.encode(user_skills)  # Convert to semantic vector

            # Determine opposite role (student -> alumni, alumni -> student)
            opposite_type = "student" if user_type == "alumni" else "alumni"

            # Fetch opposite-type users only from the same institution
            response = supabase.table("users") \
                .select("""
                    uuid, first_name, last_name, age, graduation_year, 
                    profiles(bio, skills, linkedin_url, location, profile_photo)
                """) \
                .eq("role", opposite_type) \
                .eq("institution_id", institution_id) \
                .execute()

            if response.data:
                # Convert response to DataFrame
                df = pd.DataFrame([
                    {
                        "uuid": user["uuid"],
                        "first_name": user["first_name"],
                        "last_name": user["last_name"],
                        "age": user["age"],
                        "graduation_year": user["graduation_year"],
                        "bio": user["profiles"]["bio"],
                        "skills": ", ".join(user["profiles"]["skills"]),
                        "linkedin_url": user["profiles"]["linkedin_url"],
                        "location": user["profiles"]["location"],
                        "profile_photo": user["profiles"]["profile_photo"]
                    }
                    for user in response.data if "profiles" in user and "skills" in user["profiles"]
                ])

                # Convert skills into semantic vectors
                df["vector"] = df["skills"].apply(lambda x: model.encode(x))

                # Compute Cosine Similarity
                df["similarity"] = df["vector"].apply(lambda v: np.dot(user_vector, v) / (np.linalg.norm(user_vector) * np.linalg.norm(v)))

                # Sort by similarity (highest first)
                df = df.sort_values(by="similarity", ascending=False)

                # Return full user details sorted by best match
                return JsonResponse({"matches": df.drop(columns=["vector", "similarity"]).to_dict(orient="records")}, status=200)

            return JsonResponse({"matches": []}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
