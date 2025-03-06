import jwt
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Your Stream API credentials
STREAM_API_KEY = os.environ.get("M_STREAM_SDK_API")
STREAM_API_SECRET = os.environ.get("M_STREAM_SDK_SECRET")

@csrf_exempt
def generateToken1(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")

            if not user_id:
                return JsonResponse({"error": "User ID is required"}, status=400)

            # Create JWT payload
            payload = {
                "user_id": user_id,
                "iat": datetime.datetime.utcnow(),
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),  # Token valid for 7 days
            }

            # Generate JWT token
            token = jwt.encode(payload, STREAM_API_SECRET, algorithm="HS256")

            return JsonResponse({"token": token, "api_key": STREAM_API_KEY}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
