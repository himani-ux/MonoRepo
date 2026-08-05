from django.urls import path

from .views import HelpAssistantChatView, HelpAssistantSuggestionsView, HelpAssistantStatusView


app_name = "help_assistant"

urlpatterns = [
    path("chat/", HelpAssistantChatView.as_view(), name="chat"),
    path("suggestions/", HelpAssistantSuggestionsView.as_view(), name="suggestions"),
    path("status/", HelpAssistantStatusView.as_view(), name="status"),
]
