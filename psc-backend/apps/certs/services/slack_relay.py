from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

import requests

try:
    from slack_sdk import WebClient
except ImportError:  # pragma: no cover - local fallback until requirements are installed.
    WebClient = None


DEFAULT_CERTS_SLACK_CHANNEL = "C0BMCASMNKS"
DEFAULT_OFFICE_SLACK_CHANNEL = DEFAULT_CERTS_SLACK_CHANNEL
DEFAULT_DPA_SLACK_CHANNEL = DEFAULT_CERTS_SLACK_CHANNEL
DEFAULT_TECHNICAL_SLACK_CHANNEL = DEFAULT_CERTS_SLACK_CHANNEL
DEFAULT_MARINE_SLACK_CHANNEL = DEFAULT_CERTS_SLACK_CHANNEL
SLACK_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


@dataclass(frozen=True)
class CertSlackDeliveryResult:
    attempted: bool
    delivered: bool
    channel: str
    provider_message_id: str | None = None
    error: str | None = None

    def as_delivery_status(self) -> dict[str, str]:
        status = {
            "channel": "slack",
            "status": "delivered" if self.delivered else "failed",
            "slackChannel": self.channel,
        }
        if self.provider_message_id:
            status["providerMessageId"] = self.provider_message_id
        if self.error:
            status["error"] = self.error
        return status


class CertSlackRelay:
    """Small Slack Web API wrapper for office-side Certs notifications only."""

    def __init__(
        self,
        *,
        bot_token: str | None = None,
        default_office_channel: str | None = None,
        http_post: Callable[..., Any] | None = None,
        web_client: Any | None = None,
        timeout_seconds: int = 5,
    ) -> None:
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.default_office_channel = (
            default_office_channel
            or os.getenv("CERTS_SLACK_OFFICE_CHANNEL")
            or os.getenv("SLACK_CERTS_OFFICE_CHANNEL")
            or DEFAULT_OFFICE_SLACK_CHANNEL
        )
        self.dpa_office_channel = os.getenv("CERTS_SLACK_DPA_CHANNEL") or DEFAULT_DPA_SLACK_CHANNEL
        self.technical_office_channel = (
            os.getenv("CERTS_SLACK_TECHNICAL_CHANNEL")
            or os.getenv("CERTS_SLACK_TM_CHANNEL")
            or DEFAULT_TECHNICAL_SLACK_CHANNEL
        )
        self.marine_office_channel = os.getenv("CERTS_SLACK_MARINE_CHANNEL") or DEFAULT_MARINE_SLACK_CHANNEL
        self.http_post = http_post or requests.post
        self.web_client = web_client or (WebClient(token=self.bot_token) if WebClient and self.bot_token else None)
        self.timeout_seconds = timeout_seconds

    def send_office_notification(
        self,
        *,
        channel: str,
        title: str,
        message: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        channel_value = channel or self.default_office_channel
        if not self.bot_token:
            return CertSlackDeliveryResult(
                attempted=True,
                delivered=False,
                channel=channel_value,
                error="SLACK_BOT_TOKEN not configured",
            ).as_delivery_status()

        try:
            response_payload = self._post_message(
                channel=channel_value,
                title=title,
                message=message,
                payload=payload,
            )
        except Exception as exc:
            return CertSlackDeliveryResult(
                attempted=True,
                delivered=False,
                channel=channel_value,
                error=str(exc),
            ).as_delivery_status()

        if not response_payload.get("ok"):
            return CertSlackDeliveryResult(
                attempted=True,
                delivered=False,
                channel=channel_value,
                error=str(response_payload.get("error") or "Slack API rejected message"),
            ).as_delivery_status()

        return CertSlackDeliveryResult(
            attempted=True,
            delivered=True,
            channel=channel_value,
            provider_message_id=str(response_payload.get("ts") or ""),
        ).as_delivery_status()

    def send_direct_message(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        if not self.bot_token:
            return CertSlackDeliveryResult(
                attempted=True,
                delivered=False,
                channel="slack_dm",
                error="SLACK_BOT_TOKEN not configured",
            ).as_delivery_status()

        try:
            response_payload = self._post_message(
                channel=user_id,
                title=title,
                message=message,
                payload={
                    **(payload or {}),
                    "eventType": "critical_bounce_fallback",
                },
            )
        except Exception as exc:
            return CertSlackDeliveryResult(
                attempted=True,
                delivered=False,
                channel="slack_dm",
                error=str(exc),
            ).as_delivery_status()

        if not response_payload.get("ok"):
            return CertSlackDeliveryResult(
                attempted=True,
                delivered=False,
                channel="slack_dm",
                error=str(response_payload.get("error") or "Slack API rejected direct message"),
            ).as_delivery_status()

        return CertSlackDeliveryResult(
            attempted=True,
            delivered=True,
            channel="slack_dm",
            provider_message_id=str(response_payload.get("ts") or ""),
        ).as_delivery_status()

    def _post_message(
        self,
        *,
        channel: str,
        title: str,
        message: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        body = {
            "channel": channel,
            "text": f"{title}\n{message}",
            "metadata": {
                "event_type": "certs_notification",
                "event_payload": payload or {},
            },
        }
        if self.web_client:
            return dict(self.web_client.chat_postMessage(**body))

        response = self.http_post(
            SLACK_POST_MESSAGE_URL,
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=body,
            timeout=self.timeout_seconds,
        )
        return response.json()
