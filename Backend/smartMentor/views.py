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
def mentorMatchingAlgorithm(request):
    if request.method == 'GET':
        try:
            student_id = request.GET.get("uuid")

            if not student_id:
                return JsonResponse({"error": "uuid is required"}, status=400)

            # Fetch student's profile (skills + bio)
            student_profile = supabase.table("profiles").select("skills, bio").eq("uuid", student_id).execute()
            if not student_profile.data:
                return JsonResponse({"error": "Student profile not found"}, status=404)

            student_skills = ", ".join(student_profile.data[0]["skills"])
            student_bio = student_profile.data[0]["bio"]
            student_text = student_skills + " " + student_bio
            student_vector = model.encode(student_text)

            # Fetch all mentors with institution names
            response = supabase.table("mentors") \
                .select("""
                    mentor_id, 
                    users(uuid, first_name, last_name, age, graduation_year, 
                          profiles(bio, skills, linkedin_url, location, profile_photo), 
                          institutions(name)
                    )
                """).execute()

            if response.data:
                df = pd.DataFrame([
                    {
                        "uuid": mentor["users"]["uuid"],
                        "first_name": mentor["users"]["first_name"],
                        "last_name": mentor["users"]["last_name"],
                        "age": mentor["users"]["age"],
                        "institution_name": mentor["users"]["institutions"]["name"],  # Fetch institution name
                        "graduation_year": mentor["users"]["graduation_year"],
                        "bio": mentor["users"]["profiles"]["bio"],
                        "skills": ", ".join(mentor["users"]["profiles"]["skills"]),
                        "linkedin_url": mentor["users"]["profiles"]["linkedin_url"],
                        "location": mentor["users"]["profiles"]["location"],
                        "profile_photo": mentor["users"]["profiles"]["profile_photo"]
                    }
                    for mentor in response.data if "users" in mentor and "profiles" in mentor["users"]
                ])

                df["vector"] = df.apply(lambda row: model.encode(row["skills"] + " " + row["bio"]), axis=1)
                df["similarity"] = df["vector"].apply(lambda v: np.dot(student_vector, v) / (np.linalg.norm(student_vector) * np.linalg.norm(v)))
                df = df.sort_values(by="similarity", ascending=False)

                return JsonResponse({"matches": df.drop(columns=["vector", "similarity"]).to_dict(orient="records")}, status=200)

            return JsonResponse({"matches": []}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
