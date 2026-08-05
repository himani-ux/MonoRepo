from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import answer_question, status_payload, suggested_questions


class HelpAssistantChatView(APIView):
    """Answer VIMS Help questions from file-backed documentation and optional RAG."""

    def post(self, request):
        question = str(request.data.get("question") or "").strip()
        if len(question) < 3:
            return Response(
                {"message": "Question must contain at least 3 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        context = request.data.get("context") if isinstance(request.data.get("context"), dict) else {}
        context = {
            **context,
            "user_role": getattr(request.user, "role_name", None) or getattr(request.user, "rank", None),
            "profile_id": getattr(request.user, "profile_id", None),
            "vessel_id": getattr(request.user, "vessel_id", None),
        }
        return Response(answer_question(question, context))


class HelpAssistantSuggestionsView(APIView):
    """Return deterministic context-aware starter questions."""

    def get(self, request):
        context = {
            "route": request.query_params.get("route"),
            "module": request.query_params.get("module"),
            "screen": request.query_params.get("screen"),
        }
        return Response({"suggested_questions": suggested_questions(context)})


class HelpAssistantStatusView(APIView):
    """Expose Help assistant indexing/configuration status for the UI."""

    def get(self, request):
        return Response(status_payload())
