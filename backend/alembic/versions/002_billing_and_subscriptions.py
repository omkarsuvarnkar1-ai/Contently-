"""Add billing, subscriptions, payments, and webhook event tracking tables

Revision ID: 002_billing_and_subscriptions
Revises: 001_initial_schema
Create Date: 2026-10-21 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '002_billing_and_subscriptions'
down_revision: str | None = '001_initial_schema'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_code', sa.String(length=50), nullable=False, server_default='pro_monthly'),
        sa.Column('plan_name', sa.String(length=100), nullable=False, server_default='Pro Creator Tier'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('razorpay_subscription_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_plan_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_customer_id', sa.String(length=100), nullable=True),
        sa.Column('current_start', sa.DateTime(), nullable=True),
        sa.Column('current_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_subscriptions_id', 'subscriptions', ['id'])
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('ix_subscriptions_razorpay_subscription_id', 'subscriptions', ['razorpay_subscription_id'])

    # 2. payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(length=100), nullable=False),
        sa.Column('razorpay_order_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_signature', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=True),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('error_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('razorpay_payment_id'),
    )
    op.create_index('ix_payments_id', 'payments', ['id'])
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_subscription_id', 'payments', ['subscription_id'])
    op.create_index('ix_payments_razorpay_payment_id', 'payments', ['razorpay_payment_id'])
    op.create_index('ix_payments_razorpay_order_id', 'payments', ['razorpay_order_id'])

    # 3. webhook_events table
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='processed', nullable=False),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
    )
    op.create_index('ix_webhook_events_id', 'webhook_events', ['id'])
    op.create_index('ix_webhook_events_event_id', 'webhook_events', ['event_id'])
    op.create_index('ix_webhook_events_event_type', 'webhook_events', ['event_type'])


def downgrade() -> None:
    op.drop_index('ix_webhook_events_event_type', table_name='webhook_events')
    op.drop_index('ix_webhook_events_event_id', table_name='webhook_events')
    op.drop_index('ix_webhook_events_id', table_name='webhook_events')
    op.drop_table('webhook_events')

    op.drop_index('ix_payments_razorpay_order_id', table_name='payments')
    op.drop_index('ix_payments_razorpay_payment_id', table_name='payments')
    op.drop_index('ix_payments_subscription_id', table_name='payments')
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_index('ix_payments_id', table_name='payments')
    op.drop_table('payments')

    op.drop_index('ix_subscriptions_razorpay_subscription_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_id', table_name='subscriptions')
    op.drop_table('subscriptions')
