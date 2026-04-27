import logging
import uuid
from typing import Any

import httpx

from app.besci_local.models import BeSciTextSample, BeSciTrajectoryAnalysis
from app.besci_local.service import analyze_text_samples as analyze_text_samples_local
from app.core.config import settings

logger = logging.getLogger(__name__)


class BeSciClient:
    """Remote-first BeSci client with frozen local v4.6 fallback."""

    @property
    def is_remote_configured(self) -> bool:
        return bool(settings.BESCI_API_URL and settings.BESCI_USE_REMOTE)

    @property
    def base_url(self) -> str:
        if not settings.BESCI_API_URL:
            raise ValueError("BESCI_API_URL is not configured")
        return str(settings.BESCI_API_URL).rstrip("/")

    def health(self) -> dict[str, Any]:
        if not self.is_remote_configured:
            return {"status": "local_fallback", "source": "local_besci_v4_6"}
        with httpx.Client(timeout=settings.BESCI_TIMEOUT_SECONDS) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            payload = response.json()
            payload["source"] = "remote_besci"
            return payload

    def analyze(
        self,
        samples: list[BeSciTextSample],
        *,
        user_id: uuid.UUID | None = None,
        allow_llm_summary: bool = False,
    ) -> tuple[BeSciTrajectoryAnalysis, str]:
        if self.is_remote_configured:
            try:
                with httpx.Client(timeout=settings.BESCI_TIMEOUT_SECONDS) as client:
                    response = client.post(
                        f"{self.base_url}/analyze",
                        json={
                            "samples": [sample.model_dump(mode="json") for sample in samples],
                            "allow_llm_summary": allow_llm_summary,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()["analysis"]
                    analysis = BeSciTrajectoryAnalysis.model_validate(data)
                    logger.info("BeSci analysis source=remote_besci")
                    return analysis, "remote_besci"
            except Exception as exc:
                logger.warning("Remote BeSci unavailable, source=remote_besci error=%s", exc)
                if not settings.BESCI_FALLBACK_LOCAL:
                    raise

        analysis = analyze_text_samples_local(
            samples,
            user_id=user_id,
            allow_llm_summary=False,
        )
        logger.info("BeSci analysis source=local_fallback")
        return analysis, "local_fallback"

    def chat_context(self, samples: list[BeSciTextSample]) -> str:
        if len(samples) < 2:
            return ""
        analysis, source = self.analyze(samples, allow_llm_summary=False)
        signal_names = ", ".join(signal.name for signal in analysis.signals[:3]) or "no strong pattern flags"
        factor_names = ", ".join(
            factor.name for factor in analysis.higher_order_factors if factor.score >= 0.2
        ) or "no dominant covariance factors"
        axis_names = ", ".join(
            axis.name for axis in analysis.computational_axes if abs(axis.score) >= 0.2
        ) or "no dominant neuro-computational axes"
        return (
            "Passive longitudinal BeSci context. "
            "Use as soft, non-diagnostic trend context only.\n"
            f"{analysis.summary}\n"
            f"Current interpretation: {analysis.current_state_summary}\n"
            f"Total summary: {analysis.total_summary}\n"
            f"Trajectory score: {analysis.trajectory_score:+.2f}. "
            f"Signals: {signal_names}. Factors: {factor_names}. Axes: {axis_names}. "
            f"Model: {analysis.model_version} via {analysis.representation_backend}. "
            f"Source: {source}."
        )


besci_client = BeSciClient()
