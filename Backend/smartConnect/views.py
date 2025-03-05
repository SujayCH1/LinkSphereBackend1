from django.http import JsonResponse
from .supabase import supabase
import json
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
    if request.method == 'POST':
        try:
            # Parse incoming request data
            data = json.loads(request.body)
            user_id = data.get("uuid")
            user_type = data.get("user_type")

            if not user_id or not user_type:
                return JsonResponse({"error": "uuid and user_type are required"}, status=400)

            # Determine opposite role (student -> alumni, alumni -> student)
            opposite_type = "student" if user_type == "alumni" else "alumni"

            # Fetch user profile to get their skills
            user_profile = supabase.table("profiles").select("skills").eq("uuid", user_id).execute()
            if not user_profile.data or "skills" not in user_profile.data[0]:
                return JsonResponse({"error": "User skills not found"}, status=404)

            user_skills = ", ".join(user_profile.data[0]["skills"])
            user_vector = model.encode(user_skills)  # Convert to semantic vector

            # Fetch all opposite-type users along with their skills
            response = supabase.table("users") \
                .select("uuid, role, profiles(skills)") \
                .eq("role", opposite_type) \
                .execute()


            if response.data:
                # Convert response to DataFrame
                df = pd.DataFrame([
                    {"uuid": user["uuid"], "role": user["role"], "skills": ", ".join(user["profiles"]["skills"])}
                    for user in response.data if "profiles" in user and user["profiles"]["skills"]
                ])

                # Convert skills into semantic vectors
                df["vector"] = df["skills"].apply(lambda x: model.encode(x))

                # Compute Cosine Similarity
                df["similarity"] = df["vector"].apply(lambda v: np.dot(user_vector, v) / (np.linalg.norm(user_vector) * np.linalg.norm(v)))

                # Sort by similarity (highest first)
                df = df.sort_values(by="similarity", ascending=False)

                # Return UUID and role sorted by best match
                return JsonResponse({"matches": df[["uuid", "role"]].to_dict(orient="records")}, status=200)

            return JsonResponse({"matches": []}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
