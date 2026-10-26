"""Initial database schema migration for Contently

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-10-21 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '001_initial_schema'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=100), server_default='Pro Creator', nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('handle', sa.String(length=100), server_default='omkar_builds', nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('default_engine', sa.String(length=100), server_default='Contently LLM-4x Balanced (Fine-tuned)', nullable=True),
        sa.Column('creativity_temperature', sa.Float(), server_default='0.70', nullable=True),
        sa.Column('auto_save_drafts', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('brand_voice_sync', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. workspaces table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), server_default='Contently Workspace', nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id')
    )
    op.create_index(op.f('ix_workspaces_id'), 'workspaces', ['id'], unique=False)

    # 3. content_items table
    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('format', sa.String(length=100), server_default='Social Post', nullable=True),
        sa.Column('platform', sa.String(length=100), server_default='LinkedIn', nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Draft', nullable=True),
        sa.Column('word_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('citations_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('voice_match_pct', sa.Float(), server_default='98.0', nullable=True),
        sa.Column('is_favorite', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('hero_graphic_url', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_content_items_id'), 'content_items', ['id'], unique=False)
    op.create_index(op.f('ix_content_items_user_id'), 'content_items', ['user_id'], unique=False)
    op.create_index(op.f('ix_content_items_status'), 'content_items', ['status'], unique=False)
    op.create_index(op.f('ix_content_items_is_favorite'), 'content_items', ['is_favorite'], unique=False)

    # 4. generation_history table
    op.create_table(
        'generation_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('prompt_topic', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(length=100), nullable=True),
        sa.Column('tone', sa.String(length=100), nullable=True),
        sa.Column('audience', sa.String(length=100), nullable=True),
        sa.Column('length', sa.String(length=50), nullable=True),
        sa.Column('adherence_pct', sa.Integer(), server_default='98', nullable=True),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('generated_text', sa.Text(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), server_default='0', nullable=True),
        sa.Column('word_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_generation_history_id'), 'generation_history', ['id'], unique=False)
    op.create_index(op.f('ix_generation_history_user_id'), 'generation_history', ['user_id'], unique=False)

    # 5. templates table
    op.create_table(
        'templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), server_default='social', nullable=True),
        sa.Column('format', sa.String(length=100), nullable=True),
        sa.Column('version', sa.String(length=50), server_default='v1.0', nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('formula_preview_label', sa.String(length=100), server_default='Formula Preview', nullable=True),
        sa.Column('formula_preview', sa.Text(), nullable=False),
        sa.Column('engagement_metric', sa.String(length=100), nullable=True),
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('sample_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_templates_id'), 'templates', ['id'], unique=False)
    op.create_index(op.f('ix_templates_category'), 'templates', ['category'], unique=False)

    # 6. brand_kits table
    op.create_table(
        'brand_kits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('brand_name', sa.String(length=255), nullable=True),
        sa.Column('alias_id', sa.String(length=50), server_default='#001', nullable=True),
        sa.Column('industry_verticals', sa.Text(), nullable=True),
        sa.Column('positioning_statement', sa.Text(), nullable=True),
        sa.Column('formality_pct', sa.Integer(), server_default='70', nullable=True),
        sa.Column('density_pct', sa.Integer(), server_default='85', nullable=True),
        sa.Column('edge_pct', sa.Integer(), server_default='90', nullable=True),
        sa.Column('tech_depth_pct', sa.Integer(), server_default='75', nullable=True),
        sa.Column('preferred_keywords', sa.Text(), nullable=True),
        sa.Column('forbidden_keywords', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_brand_kits_id'), 'brand_kits', ['id'], unique=False)

    # 7. scheduled_posts table
    op.create_table(
        'scheduled_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('platform', sa.String(length=100), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(), nullable=False),
        sa.Column('time_slot_label', sa.String(length=50), server_default='09:30 AM', nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Scheduled', nullable=True),
        sa.Column('day_of_month', sa.Integer(), server_default='20', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_scheduled_posts_id'), 'scheduled_posts', ['id'], unique=False)
    op.create_index(op.f('ix_scheduled_posts_user_id'), 'scheduled_posts', ['user_id'], unique=False)

    # 8. seo_analyses table
    op.create_table(
        'seo_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('target_keyword', sa.String(length=255), nullable=False),
        sa.Column('density_pct', sa.Float(), server_default='2.1', nullable=True),
        sa.Column('occurrences', sa.Integer(), server_default='8', nullable=True),
        sa.Column('total_words', sa.Integer(), server_default='1480', nullable=True),
        sa.Column('serp_meta_title', sa.String(length=255), nullable=True),
        sa.Column('serp_meta_description', sa.Text(), nullable=True),
        sa.Column('serp_url', sa.String(length=255), nullable=True),
        sa.Column('seo_score', sa.Integer(), server_default='92', nullable=True),
        sa.Column('suggestions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_seo_analyses_id'), 'seo_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_seo_analyses_user_id'), 'seo_analyses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('seo_analyses')
    op.drop_table('scheduled_posts')
    op.drop_table('brand_kits')
    op.drop_table('templates')
    op.drop_table('generation_history')
    op.drop_table('content_items')
    op.drop_table('workspaces')
    op.drop_table('users')
