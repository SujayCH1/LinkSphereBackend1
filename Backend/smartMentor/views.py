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
def mentorMatchingAlgorithm(request):
    if request.method == 'POST':
        try:
            # Parse incoming request data
            data = json.loads(request.body)
            student_id = data.get("uuid")

            if not student_id:
                return JsonResponse({"error": "uuid is required"}, status=400)

            # Fetch student's profile (bio + skills)
            student_profile = supabase.table("profiles").select("skills, bio").eq("uuid", student_id).execute()
            if not student_profile.data:
                return JsonResponse({"error": "Student profile not found"}, status=404)

            student_skills = ", ".join(student_profile.data[0]["skills"])
            student_bio = student_profile.data[0]["bio"]

            # Combine bio and skills for embedding
            student_text = student_skills + " " + student_bio
            student_vector = model.encode(student_text)  # Convert to semantic vector

            # Fetch all mentors (users that exist in mentors table)
            response = supabase.table("mentors") \
                .select("mentor_id, users(uuid, profiles(skills, bio))") \
                .execute()

            if response.data:
                # Convert response to DataFrame
                df = pd.DataFrame([
                    {
                        "uuid": mentor["users"]["uuid"],
                        "skills": ", ".join(mentor["users"]["profiles"]["skills"]),
                        "bio": mentor["users"]["profiles"]["bio"]
                    }
                    for mentor in response.data if "users" in mentor and "profiles" in mentor["users"]
                ])

                # Convert skills + bio into semantic vectors
                df["vector"] = df.apply(lambda row: model.encode(row["skills"] + " " + row["bio"]), axis=1)

                # Compute Cosine Similarity
                df["similarity"] = df["vector"].apply(lambda v: np.dot(student_vector, v) / (np.linalg.norm(student_vector) * np.linalg.norm(v)))

                # Sort by similarity (highest first)
                df = df.sort_values(by="similarity", ascending=False)

                # Return UUIDs of best mentors
                return JsonResponse({"matches": df["uuid"].tolist()}, status=200)

            return JsonResponse({"matches": []}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
