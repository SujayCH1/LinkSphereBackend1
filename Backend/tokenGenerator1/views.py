import jwt
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
from dotenv import load_dotenv

load_dotenv()

STREAM_API_KEY = os.environ.get("M_STREAM_SDK_API")
STREAM_API_SECRET = os.environ.get("M_STREAM_SDK_SECRET")

@csrf_exempt
def generateToken1(request):
    if request.method == 'GET':
        try:
            uuid = request.GET.get("uuid")

            if not uuid:
                return JsonResponse({"error": "User ID is required"}, status=400)

            payload = {
                "uuid": uuid,
                "iat": datetime.datetime.utcnow(),
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            }

            token = jwt.encode(payload, STREAM_API_SECRET, algorithm="HS256")

            return JsonResponse({"token": token}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
