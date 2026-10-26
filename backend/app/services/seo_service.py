import re

from backend.app.schemas.seo import (
    KeywordDensityResult,
    SeoAnalyzeResponse,
    SerpPreview,
)
from backend.app.services.ai_service import AiService


class SeoService:

    @classmethod
    def analyze_text(
        cls,
        content: str,
        target_keyword: str = "AI in education",
        tracked_keywords: list[str] | None = None,
        meta_title: str | None = None,
        meta_description: str | None = None,
    ) -> SeoAnalyzeResponse:
        """Calculate real keyword density, occurrences, SERP simulator parameters, and SEO score."""
        words = re.findall(r"\b\w+\b", content.lower())
        total_words = max(1, len(words))

        def calc_density(kw: str):
            kw_cleaned = kw.strip().lower()
            kw_words = re.findall(r"\b\w+\b", kw_cleaned)
            kw_len = len(kw_words)
            if kw_len == 0:
                return 0, 0.0

            # Count occurrences using case-insensitive regex
            pattern = r"\b" + r"\s+".join(re.escape(w) for w in kw_words) + r"\b"
            matches = len(re.findall(pattern, content.lower()))
            density = round((matches * kw_len / total_words) * 100, 1)
            return matches, density

        # Primary target
        prim_matches, prim_density = calc_density(target_keyword)
        if prim_density < 1.0:
            prim_status = "Under-optimized (< 1.5%)"
        elif prim_density <= 2.5:
            prim_status = "Ideal Range (1.5% - 2.5%)"
        else:
            prim_status = "Over-optimized (> 2.5%)"

        primary_result = KeywordDensityResult(
            keyword=target_keyword,
            occurrences=prim_matches,
            density_pct=prim_density,
            context="Heading & Body match",
            status=prim_status,
        )

        # Tracked secondary keywords
        default_tracked = ["personalized learning", "LLM tutors", "adaptive educational software"]
        to_track = tracked_keywords if tracked_keywords else default_tracked

        tracked_results = []
        for kw in to_track:
            m, d = calc_density(kw)
            tracked_results.append(
                KeywordDensityResult(
                    keyword=kw,
                    occurrences=m,
                    density_pct=d,
                    context="Body context",
                    status="Tracked",
                )
            )

        # Meta title & description analysis
        title = meta_title or f"{target_keyword.title()}: Transforming Modern Classrooms with LLMs"
        desc = (
            meta_description
            or "Discover how universities and modern educators leverage AI tutoring agents to reduce grading time by 85% while boosting student inquiry."
        )

        title_len = len(title)
        desc_len = len(desc)

        title_status = "Optimal (50-60 chars)" if 45 <= title_len <= 65 else f"Length: {title_len} chars"
        desc_status = "No truncation expected" if desc_len <= 160 else "Warning: may truncate in SERP"

        serp_preview = SerpPreview(
            title=title,
            description=desc,
            url="https://contently.ai > blog > ai-in-education-modern-classrooms",
            title_char_count=title_len,
            desc_char_count=desc_len,
            title_status=title_status,
            desc_status=desc_status,
        )

        # Scoring logic
        score = 80
        if 1.5 <= prim_density <= 2.5:
            score += 10
        elif prim_density > 0:
            score += 5

        if 45 <= title_len <= 65:
            score += 5
        if 120 <= desc_len <= 160:
            score += 5

        suggestions = [
            "Add 'classroom AI policy' (+14% search volume, low competition)",
            f"Ensure '{target_keyword}' appears in H1 heading and first 100 words",
        ]
        if prim_density < 1.5:
            suggestions.append(f"Increase usage of '{target_keyword}' to reach 1.8% density.")
        if desc_len > 160:
            suggestions.append("Trim meta description to under 160 characters to prevent Google truncation.")

        return SeoAnalyzeResponse(
            seo_score=min(99, score),
            word_count=total_words,
            primary_target=primary_result,
            tracked_keywords=tracked_results,
            serp_preview=serp_preview,
            suggestions=suggestions,
        )

    @classmethod
    async def rewrite_serp(
        cls,
        target_keyword: str,
        current_title: str | None = None,
        current_description: str | None = None,
        provider: str | None = None,
    ) -> dict:
        """Call AI provider to synthesize high-CTR SERP metadata."""
        prompt = (
            f"Write a high-CTR Google SEO Meta Title (under 60 chars) and Meta Description (under 155 chars) "
            f"targeting the keyword '{target_keyword}'.\n"
            f"Current title: {current_title}\n"
            f"Current description: {current_description}\n"
            f"Format response as:\nTITLE: [title]\nDESCRIPTION: [description]"
        )

        res = await AiService.generate_content(
            prompt_topic=prompt,
            channel="blog",
            tone="Analytical & Direct",
            length="short",
            provider=provider,
        )
        text = res["generated_text"]

        title = f"{target_keyword.title()} in 2026: Complete Strategy Guide"
        description = (
            f"Comprehensive analysis and tactical frameworks for {target_keyword}. "
            f"Learn how to optimize performance and scale results today."
        )

        lines = text.split("\n")
        for line in lines:
            if line.upper().startswith("TITLE:"):
                title = line.replace("TITLE:", "").replace("Title:", "").strip()
            elif line.upper().startswith("DESCRIPTION:"):
                description = (
                    line.replace("DESCRIPTION:", "").replace("Description:", "").strip()
                )

        return {
            "suggested_title": title,
            "suggested_description": description,
            "target_keyword": target_keyword,
        }
