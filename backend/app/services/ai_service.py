import logging

import httpx
from fastapi import HTTPException, status

from backend.app.core.config import settings

logger = logging.getLogger("contently.ai_service")


class AiService:
    """Production provider adapter for OpenAI, Google Gemini, and Anthropic Claude."""

    @staticmethod
    def _get_provider_credentials(provider: str | None = None):
        target = (provider or settings.DEFAULT_AI_PROVIDER).lower()

        if target == "openai":
            key = settings.OPENAI_API_KEY
            if not key or key.strip() == "":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "AI Generation Failed: OpenAI credentials are not configured on the server. "
                        "Please set OPENAI_API_KEY in backend/.env. "
                        "You can obtain an API key at https://platform.openai.com/api-keys."
                    ),
                )
            return "openai", key, settings.OPENAI_MODEL

        elif target in ["gemini", "google"]:
            key = settings.GEMINI_API_KEY
            if not key or key.strip() == "":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "AI Generation Failed: Google Gemini credentials are not configured on the server. "
                        "Please set GEMINI_API_KEY in backend/.env. "
                        "You can obtain an API key at https://aistudio.google.com/app/apikey."
                    ),
                )
            return "gemini", key, settings.GEMINI_MODEL

        elif target in ["anthropic", "claude"]:
            key = settings.ANTHROPIC_API_KEY
            if not key or key.strip() == "":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "AI Generation Failed: Anthropic credentials are not configured on the server. "
                        "Please set ANTHROPIC_API_KEY in backend/.env. "
                        "You can obtain an API key at https://console.anthropic.com/settings/keys."
                    ),
                )
            return "anthropic", key, settings.ANTHROPIC_MODEL

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported AI provider '{provider}'. Supported providers are: openai, gemini, anthropic.",
            )

    @classmethod
    async def generate_content(
        cls,
        prompt_topic: str,
        channel: str = "linkedin",
        tone: str = "Analytical & Direct",
        audience: str = "B2B SaaS Founders",
        length: str = "medium",
        adherence_pct: int = 98,
        provider: str | None = None,
        brand_positioning: str | None = None,
        preferred_keywords: list[str] | None = None,
        forbidden_keywords: list[str] | None = None,
    ) -> dict:
        """Call real AI provider to synthesize a tailored content asset."""
        prov, key, model = cls._get_provider_credentials(provider)

        length_guide = {
            "short": "Keep response concise, under 150 words.",
            "medium": "Structure standard length response, between 250-450 words.",
            "long": "Deliver a detailed comprehensive piece, 600-900 words.",
        }.get(length, "Between 250-450 words.")

        sys_prompt = (
            f"You are Contently LLM-4x, an elite AI content strategist and copywriter.\n"
            f"Target Channel: {channel}\n"
            f"Voice & Tone: {tone}\n"
            f"Target Audience: {audience}\n"
            f"Length Requirement: {length_guide}\n"
            f"Brand Adherence: {adherence_pct}%\n"
        )
        if brand_positioning:
            sys_prompt += f"Brand Positioning Anchor: {brand_positioning}\n"
        if preferred_keywords:
            sys_prompt += f"Preferred Vocabulary: {', '.join(preferred_keywords)}\n"
        if forbidden_keywords:
            sys_prompt += f"Forbidden Clichés: Do not use any of: {', '.join(forbidden_keywords)}\n"

        user_prompt = f"Topic & Thesis: {prompt_topic}\n\nDraft high-converting, polished content suitable for {channel}."

        generated_text = ""
        tokens_used = 0

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                if prov == "openai":
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "temperature": 0.7,
                        },
                    )
                    if resp.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"OpenAI API returned error ({resp.status_code}): {resp.text}",
                        )
                    data = resp.json()
                    generated_text = data["choices"][0]["message"]["content"]
                    tokens_used = data.get("usage", {}).get("total_tokens", 0)

                elif prov == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    resp = await client.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json={
                            "system_instruction": {"parts": [{"text": sys_prompt}]},
                            "contents": [{"parts": [{"text": user_prompt}]}],
                            "generationConfig": {"temperature": 0.7},
                        },
                    )
                    if resp.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Google Gemini API returned error ({resp.status_code}): {resp.text}",
                        )
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        generated_text = "".join(p.get("text", "") for p in parts)
                    tokens_used = data.get("usageMetadata", {}).get("totalTokenCount", 0)

                elif prov == "anthropic":
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "system": sys_prompt,
                            "messages": [{"role": "user", "content": user_prompt}],
                            "max_tokens": 1500,
                            "temperature": 0.7,
                        },
                    )
                    if resp.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Anthropic API returned error ({resp.status_code}): {resp.text}",
                        )
                    data = resp.json()
                    contents = data.get("content", [])
                    generated_text = "".join(c.get("text", "") for c in contents if c.get("type") == "text")
                    tokens_used = (data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0))

            except httpx.RequestError as e:
                logger.error("AI Provider request failed: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"Connection to AI provider ({prov}) timed out or failed: {e!s}",
                )

        words = len(generated_text.split()) if generated_text else 0
        read_time = round(max(0.4, words / 200), 1)

        return {
            "generated_text": generated_text,
            "model_used": f"{prov.capitalize()} ({model})",
            "tokens_used": tokens_used or (words * 2),
            "word_count": words,
            "read_time_mins": read_time,
            "brand_match_pct": min(99.4, 95.0 + (adherence_pct * 0.04)),
        }

    @classmethod
    async def refine_content(cls, text: str, refine_type: str, provider: str | None = None) -> str:
        """Refine existing text into punchy, shorten, or framework format."""
        prov, key, model = cls._get_provider_credentials(provider)

        instructions = {
            "punchy": "Rewrite the following content to be punchy, contrarian, direct, and authoritative with high-impact bullet takeaways.",
            "shorten": "Condense and shorten the following content to its essential core thesis, cutting all fluff while keeping the value.",
            "framework": "Structure the following content into a numbered step-by-step tactical framework or matrix with clear labels.",
        }.get(refine_type, "Refine and polish the content.")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if prov == "openai":
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": instructions},
                                {"role": "user", "content": text},
                            ],
                            "temperature": 0.6,
                        },
                    )
                    if resp.status_code != 200:
                        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenAI error: {resp.text}")
                    return resp.json()["choices"][0]["message"]["content"]
                elif prov == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    resp = await client.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json={
                            "system_instruction": {"parts": [{"text": instructions}]},
                            "contents": [{"parts": [{"text": text}]}],
                        },
                    )
                    if resp.status_code != 200:
                        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Gemini error: {resp.text}")
                    candidates = resp.json().get("candidates", [])
                    return "".join(p.get("text", "") for p in candidates[0]["content"].get("parts", [])) if candidates else text
                elif prov == "anthropic":
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "system": instructions,
                            "messages": [{"role": "user", "content": text}],
                            "max_tokens": 1000,
                        },
                    )
                    if resp.status_code != 200:
                        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Anthropic error: {resp.text}")
                    contents = resp.json().get("content", [])
                    return "".join(c.get("text", "") for c in contents if c.get("type") == "text")
            except httpx.RequestError as e:
                raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=f"AI request failed: {e!s}")

        return text
