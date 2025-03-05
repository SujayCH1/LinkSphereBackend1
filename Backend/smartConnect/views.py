from django.shortcuts import render
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
            data = json.loads(request.body)
            user_id = data.get("uuid")
            user_type = data.get("user_type")

            if not user_id or not user_type:
                return JsonResponse({"error": "UUID and user_type are required"}, status=400)
            
            opposite_type = "student" if user_type == "alumni" else "alumni"

            # Fetch users along with their skills
            response = supabase.table("users") \
                .select("uuid, profiles(skills)") \
                .eq("role", opposite_type) \
                .execute()

            if response.data:
                # Convert response to DataFrame
                df = pd.DataFrame([
                    {"uuid": user["uuid"], "skills": ", ".join(user["profiles"]["skills"])} 
                    for user in response.data if "profiles" in user and user["profiles"]["skills"]
                ])

                # Convert skills into semantic vectors
                df["vector"] = df["skills"].apply(lambda x: model.encode(x))

                # Convert vectors to list for JSON response
                df["vector"] = df["vector"].apply(lambda x: x.tolist())

                return JsonResponse({"matches": df.to_dict(orient="records")}, status=200)
            
            return JsonResponse({"matches": []}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    return JsonResponse({"error": "Invalid request method"}, status=405)
