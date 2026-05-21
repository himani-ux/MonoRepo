from __future__ import annotations

from rest_framework import serializers

from apps.safety.models import CorrectiveAction, Incident, Recommendation, RecommendationVerification
from apps.safety.services.deadline_pauser import DeadlinePauser
from apps.safety.services.pic_retention import PicRetentionService


def _latest_verification(recommendation: Recommendation) -> RecommendationVerification | None:
    return recommendation.verifications.order_by("-verified_at", "-id").first()


def _is_deferred(latest: RecommendationVerification | None) -> bool:
    if latest is None:
        return False
    return (latest.notes or "").strip().upper().startswith("DEFERRED:")


class RecommendationVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationVerification
        fields = (
            "public_id",
            "recommendation_id",
            "is_effective",
            "residual_risk",
            "verified_at",
            "verified_by",
            "notes",
        )


class IncidentPhase8VerifySerializer(serializers.Serializer):
    recommendation_id = serializers.IntegerField(min_value=1)
    is_effective = serializers.BooleanField()
    residual_risk = serializers.CharField(max_length=32)
    notes = serializers.CharField(allow_blank=False)

    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        try:
            recommendation = incident.recommendations.get(pk=attrs["recommendation_id"], is_deleted=False)
        except Recommendation.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"recommendation_id": "Recommendation must belong to the incident being verified."}
            ) from exc
        attrs["recommendation"] = recommendation
        return attrs


class IncidentPhase8CloseSerializer(serializers.Serializer):
    closure_reason = serializers.CharField(allow_blank=False)


def build_phase8_workspace_payload(incident: Incident) -> dict[str, object]:
    recommendations = list(
        incident.recommendations.filter(is_deleted=False)
        .prefetch_related("verifications", "corrective_actions")
        .order_by("id")
    )
    recommendation_rows: list[dict[str, object]] = []
    blocker_codes: list[str] = []
    corrective_actions_summary = {
        "total": 0,
        "open": 0,
        "in_progress": 0,
        "pending_verify": 0,
        "closed": 0,
    }
    physical_verification_done = 0
    physical_verification_pending = 0

    for recommendation in recommendations:
        corrective_actions = [
            action
            for action in recommendation.corrective_actions.all()
            if not action.is_deleted
        ]
        latest_verification = _latest_verification(recommendation)
        action_completed = True
        for action in corrective_actions:
            corrective_actions_summary["total"] += 1
            if action.status == CorrectiveAction.Status.OPEN:
                corrective_actions_summary["open"] += 1
                action_completed = False
            elif action.status == CorrectiveAction.Status.IN_PROGRESS:
                corrective_actions_summary["in_progress"] += 1
                action_completed = False
            elif action.status == CorrectiveAction.Status.PENDING_VERIFY:
                corrective_actions_summary["pending_verify"] += 1
                action_completed = False
            elif action.status == CorrectiveAction.Status.CLOSED:
                corrective_actions_summary["closed"] += 1

            if action.physical_verification_done:
                physical_verification_done += 1
            else:
                physical_verification_pending += 1

        deferred = _is_deferred(latest_verification)
        if latest_verification is None:
            blocker_codes.append(f"pending_verification:{recommendation.pk}")
        elif not latest_verification.is_effective and not deferred:
            blocker_codes.append(f"ineffective_verification:{recommendation.pk}")

        if corrective_actions and not action_completed and not deferred:
            blocker_codes.append(f"open_corrective_actions:{recommendation.pk}")

        recommendation_rows.append(
            {
                "id": recommendation.pk,
                "tier": recommendation.tier,
                "title": recommendation.title,
                "action_completed": action_completed,
                "verification_deferred": deferred,
                "corrective_action_count": len(corrective_actions),
                "latest_verification": (
                    RecommendationVerificationSerializer(latest_verification).data
                    if latest_verification is not None
                    else None
                ),
            }
        )

    if not recommendations:
        blocker_codes.append("no_recommendations")

    deadline_pause = DeadlinePauser().status_for_incident(incident)
    pic_retention = PicRetentionService().current_status(incident)

    return {
        "incident_id": incident.pk,
        "current_phase": incident.current_phase,
        "state": incident.state,
        "risk_band": incident.risk_band,
        "required_process_id": "SAF_P_005" if incident.risk_band == Incident.RiskBand.RED else "SAF_P_004",
        "recommendations": recommendation_rows,
        "corrective_actions_summary": corrective_actions_summary,
        "physical_verification": {
            "done": physical_verification_done,
            "pending": physical_verification_pending,
            "separate_track": True,
        },
        "deadline_pause": deadline_pause,
        "pic_retention": pic_retention,
        "ready_for_close": not blocker_codes,
        "blockers": blocker_codes,
    }
