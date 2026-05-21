from __future__ import annotations

from django.http import JsonResponse


def safety_api_root(request):
    if not request.headers.get("Authorization"):
        return JsonResponse(
            {"detail": "Authentication credentials were not provided."},
            status=401,
        )

    return JsonResponse({"detail": "Safety API root placeholder."})
