from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.models.billing import Subscription
from backend.app.models.brand_kit import BrandKit
from backend.app.models.content import ContentItem
from backend.app.models.planner import ScheduledPost
from backend.app.models.template import Template
from backend.app.models.user import User, Workspace


class SeedService:

    @classmethod
    def seed_initial_data(cls, db: Session) -> User:
        """Seed demo account, initial content library, templates catalog, and planner items."""
        # 1. User
        user = db.query(User).filter(User.email == settings.DEMO_USER_EMAIL).first()
        if not user:
            user = User(
                email=settings.DEMO_USER_EMAIL,
                full_name=settings.DEMO_USER_NAME,
                hashed_password=hash_password(settings.DEMO_USER_PASSWORD),
                role=settings.DEMO_USER_ROLE,
                avatar_url=settings.DEMO_USER_AVATAR,
                handle="omkar_builds",
                bio="Founding creator & AI technologist crafting multi-channel distribution systems.",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            workspace = Workspace(name="Omkar's Workspace", owner_id=user.id)
            db.add(workspace)

            brand_kit = BrandKit(
                user_id=user.id,
                brand_name="Contently / Omkar",
                alias_id="#001",
                industry_verticals="B2B SaaS, Artificial Intelligence, Developer Tools",
                positioning_statement="High-leverage AI-native content strategy for modern B2B founders and engineering leads",
                formality_pct=70,
                density_pct=85,
                edge_pct=90,
                tech_depth_pct=75,
                preferred_keywords="leverage,paradigm shift,deterministic,first-principles,signal-to-noise ratio,operational velocity",
                forbidden_keywords="game-changer,unleash,delve,supercharge,revolutionary,in today's fast-paced world",
            )
            db.add(brand_kit)
            db.commit()

        # 2. Content Library Items
        existing_content = db.query(ContentItem).filter(ContentItem.user_id == user.id).first()
        if not existing_content:
            now = datetime.now(UTC)
            items = [
                ContentItem(
                    user_id=user.id,
                    title="AI in Education: Transforming Modern Classrooms",
                    body="""Most universities still treat Artificial Intelligence like a calculator in a 1980s calculus test: something dangerous to ban from exams rather than a force-multiplier for intellectual autonomy.

Personalized tutoring loops are outpacing standard standardized instruction models. Over 68% of enterprise EdTech institutions have shifted toward autonomous evaluation matrices.

Key Takeaways:
1. Real-time Socratic QA boosts retention by 3.4x.
2. Formative evaluations eliminate 40% of repetitive grading friction.
3. Closed deterministic guardrails protect academic integrity without hindering curiosity.""",
                    excerpt="Personalized tutoring loops are outpacing standard standardized instruction models. Over 68% of enterprise EdTech institutions have shifted toward autonomous evaluation matrices...",
                    format="Thought Piece",
                    platform="LinkedIn",
                    status="Saved",
                    word_count=854,
                    citations_count=3,
                    voice_match_pct=98.0,
                    is_favorite=True,
                    hero_graphic_url="https://lh3.googleusercontent.com/aida-public/AB6AXuD5-avg5jTp88ghoCE5C_UqeD4-M0GKWQ85FVhJHtmHuxlzzHCwL15UIiSK3MfZAvsPEUBhR3-yHuXj1n3hFNx2I10B8GYRkkNCGKASSBlBlhm5V5XiZcR4TPsQZFBWjaS0yIyR5ylpeDkqMdTPmhWpWAEIlglKNDf5wITQF2WKxAG4gjWkb2U7X_pTR3ufm1tIYD123Au2569SJ2QJgFrGJIswok9zxPa7RO4-XDM",
                    created_at=now - timedelta(hours=2),
                    updated_at=now - timedelta(hours=2),
                ),
                ContentItem(
                    user_id=user.id,
                    title="10x Your Productivity with Prompt Frameworks",
                    body="""I spent 120 hours dissecting top enterprise prompt architectures.
You can master the exact 7-step system in 4 minutes (bookmark this):

1. Explicit role framing: Always declare context and constraint boundaries first.
2. Few-shot validation: Feed 2 exemplary input/output pairs to calibrate tone.
3. Negative prompt guardrails: Declare prohibited cliches directly.
4. Schema bounding: Demand strict JSON or Markdown hierarchy.
5. Verification loop: Ask the model to score its own adherence before final output.""",
                    excerpt="Thread of 7 posts · 4 visuals planned. Tactical playbook architecture optimized for aggressive bookmark rates...",
                    format="Viral Thread",
                    platform="Twitter / X",
                    status="Draft",
                    word_count=420,
                    citations_count=1,
                    voice_match_pct=96.0,
                    is_favorite=False,
                    created_at=now - timedelta(days=1),
                    updated_at=now - timedelta(days=1),
                ),
                ContentItem(
                    user_id=user.id,
                    title="Startup Launch: The Zero to One Playbook",
                    body="""Launching in 2026 isn't about press releases—it's about compounding organic resonance loops across niche technical communities.

Carousel Breakdown:
- Slide 1: Why conventional launch playbooks waste 80% of ad spend.
- Slide 2: Building your proof-of-work distribution moat before coding.
- Slide 3: Synthesizing 5 platform assets from one technical spec sheet.""",
                    excerpt="Carousel caption · 24 tagged accounts. Engaging story captions with curated hashtags and carousel retention strategies.",
                    format="Multi-image Caption",
                    platform="Instagram",
                    status="Scheduled",
                    word_count=610,
                    citations_count=2,
                    voice_match_pct=94.5,
                    is_favorite=False,
                    scheduled_at=now + timedelta(days=3),
                    created_at=now - timedelta(days=2),
                    updated_at=now - timedelta(days=2),
                ),
                ContentItem(
                    user_id=user.id,
                    title="The Future of Autonomous AI Agents in 2026",
                    body="""Autonomous agentic feedback loops are quietly obsoleting monolithic SaaS glue code.

Here is the operational blueprint:
1. Micro-agent routing: Specialized 8B parameter models executing deterministic tasks.
2. Self-healing state machines: Recovering gracefully from API rate limits.
3. Observability telemetry: Real-time cost and latency attribution per decision token.""",
                    excerpt="Comprehensive whitepaper examining multi-agent orchestration, deterministic latency guardrails, and unit economics.",
                    format="Long-form Guide",
                    platform="Tech Blog",
                    status="Published",
                    word_count=2410,
                    citations_count=8,
                    voice_match_pct=99.1,
                    is_favorite=True,
                    published_at=now - timedelta(days=3),
                    created_at=now - timedelta(days=4),
                    updated_at=now - timedelta(days=3),
                ),
            ]
            for it in items:
                db.add(it)
            db.commit()

        # 3. Scheduled Posts
        existing_planner = db.query(ScheduledPost).filter(ScheduledPost.user_id == user.id).first()
        if not existing_planner:
            now = datetime.now(UTC)
            planner_items = [
                ScheduledPost(
                    user_id=user.id,
                    title="The 4-Hour Editorial Machine",
                    platform="LinkedIn",
                    scheduled_time=now + timedelta(days=1),
                    time_slot_label="09:30 AM",
                    status="Scheduled",
                    day_of_month=20,
                ),
                ScheduledPost(
                    user_id=user.id,
                    title="Thread: 7 Mental Models for Prompt Engineers",
                    platform="X / Twitter",
                    scheduled_time=now + timedelta(days=2),
                    time_slot_label="02:00 PM",
                    status="Scheduled",
                    day_of_month=21,
                ),
                ScheduledPost(
                    user_id=user.id,
                    title="Q4 Content Calibration Blueprint",
                    platform="Blog",
                    scheduled_time=now + timedelta(days=3),
                    time_slot_label="11:00 AM",
                    status="Scheduled",
                    day_of_month=24,
                ),
                ScheduledPost(
                    user_id=user.id,
                    title="Weekly Creator Intelligence Newsletter",
                    platform="Newsletter",
                    scheduled_time=now + timedelta(days=5),
                    time_slot_label="08:00 AM",
                    status="Scheduled",
                    day_of_month=26,
                ),
            ]
            for p in planner_items:
                db.add(p)
            db.commit()

        # 4. Templates Catalog
        if db.query(Template).count() == 0:
            templates = [
                Template(
                    title="The Contrarian Thought Leader",
                    category="social",
                    format="LinkedIn • High CTR",
                    version="v2.4",
                    description="Challenge prevailing industry consensus with data-backed alternative viewpoints and structured rebuttal arcs.",
                    formula_preview_label="Formula Preview",
                    formula_preview="“Most leaders believe [Conventional Metric] is king. Here is why the fastest 1% abandoned it in 2026:”",
                    engagement_metric="4.2x Avg Engagement",
                    usage_count=1840,
                    sample_body="Most industry leaders believe volume is king. Here is why the fastest 1% abandoned that playbook in 2026...",
                ),
                Template(
                    title="The 10x Framework Breakdown",
                    category="social",
                    format="X / Twitter • Viral Thread",
                    version="v3.1",
                    description="Step-by-step tactical playbook architecture optimized for aggressive bookmark rates and quote-retweet spikes.",
                    formula_preview_label="Thread Starter Hook",
                    formula_preview="“I spent 120 hours dissecting [Competitor Playbook]. You can master the exact system in 4 minutes (bookmark this):”",
                    engagement_metric="14.8% Save Rate",
                    usage_count=3210,
                    sample_body="I spent 120 hours dissecting top enterprise prompt architectures. You can master the exact system in 4 minutes...",
                ),
                Template(
                    title="Technical Deep-Dive Case Study",
                    category="longform",
                    format="Blog • SEO Optimized",
                    version="v1.8",
                    description="Deconstruct complex architectural migrations, performance benchmarks, and post-mortem incident resolution matrices.",
                    formula_preview_label="Thesis Anchor",
                    formula_preview="“How we reduced p99 inference latency by 74% while processing 40M tokens daily without cloud lock-in.”",
                    engagement_metric="6.8 min Avg Read Time",
                    usage_count=980,
                    sample_body="How we reduced p99 inference latency by 74% while scaling our multi-tenant retrieval pipelines...",
                ),
                Template(
                    title="The Executive Sunday Memo",
                    category="newsletters",
                    format="Newsletter • High Open-Rate",
                    version="v2.0",
                    description="Curated weekly synthesis delivering 3 high-signal takeaways, 2 mental models, and 1 actionable implementation prompt.",
                    formula_preview_label="Subject Line Formula",
                    formula_preview="“The Signal [Issue #48]: Why autonomous AI loops are replacing pipeline glue”",
                    engagement_metric="52.4% Open Rate",
                    usage_count=1450,
                    sample_body="Happy Sunday. This week we break down 3 quiet shifts in agentic infrastructure...",
                ),
                Template(
                    title="The 60-Second Viral Hook Reel",
                    category="video",
                    format="Video Script • Reels / Shorts",
                    version="v1.2",
                    description="3-second retention hook followed by rapid pattern-interrupt visual cues and a conversion call-to-action outro.",
                    formula_preview_label="Hook Cue",
                    formula_preview="“[Visual Pattern Interrupt]: If you are still using manual workflows for [Task], stop scrolling right now.”",
                    engagement_metric="82% Completion Rate",
                    usage_count=2150,
                    sample_body="If you are still using manual workflows for multi-channel content distribution, stop scrolling right now...",
                ),
                Template(
                    title="Product Launch Teaser Announcement",
                    category="social",
                    format="LinkedIn / X • Announcement",
                    version="v2.2",
                    description="Build anticipation and waitlist velocity for private beta releases and milestone platform updates.",
                    formula_preview_label="Announcement Hook",
                    formula_preview="“After 6 months in stealth, we are finally opening early access to [Platform Name]:”",
                    engagement_metric="3.8x Click Through",
                    usage_count=1620,
                    sample_body="After 6 months in stealth, we are finally opening early access to Contently Studio...",
                ),
            ]
            for t in templates:
                db.add(t)
            db.commit()

        # 3. Ensure active subscription record exists for user
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if not sub:
            now = datetime.now(UTC)
            demo_sub = Subscription(
                user_id=user.id,
                plan_code="pro_monthly",
                plan_name="Pro Creator Tier",
                status="active",
                current_start=now,
                current_end=now + timedelta(days=30),
                cancel_at_period_end=False,
            )
            db.add(demo_sub)
            db.commit()

        return user
