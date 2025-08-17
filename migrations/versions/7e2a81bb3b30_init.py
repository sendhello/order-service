""""init"

Revision ID: 7e2a81bb3b30
Revises: 
Create Date: 2025-08-16 19:08:41.237088

"""
from alembic import op
import sqlalchemy as sa
from db import postgres


# revision identifiers, used by Alembic.
revision = '7e2a81bb3b30'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('parties',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('company', sa.String(length=255), nullable=True),
    sa.Column('address', sa.Text(), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('additional', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('org_id', 'phone', 'address', 'first_name', 'last_name', name='uq_org_parties_unique')
    )
    op.create_index('ix_org_parties_address', 'parties', ['org_id', 'address'], unique=False)
    op.create_index('ix_org_parties_company', 'parties', ['org_id', 'company'], unique=False)
    op.create_table('orders',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('CREATED', 'ASSIGNED', 'IN_PROGRESS', 'DELIVERED', 'CANCELLED', name='order_status'), nullable=False),
    sa.Column('source', sa.String(length=100), nullable=True),
    sa.Column('delivery_service_level', sa.Enum('STANDARD', 'EXPRESS', name='delivery_service_level'), nullable=False),
    sa.Column('tracking_id', sa.UUID(), nullable=False),
    sa.Column('payment_method', sa.Enum('PREPAID', 'CASH_ON_DELIVERY', 'CARD_ON_DELIVERY', name='payment_method'), nullable=False),
    sa.Column('payment_status', sa.Boolean(), nullable=False),
    sa.Column('payment_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('insurance_number', sa.String(length=100), nullable=True),
    sa.Column('special_instructions', sa.Text(), nullable=True),
    sa.Column('additional', sa.Text(), nullable=True),
    sa.Column('sender_id', sa.UUID(), nullable=True),
    sa.Column('recipient_id', sa.UUID(), nullable=False),
    sa.Column('courier_id', sa.UUID(), nullable=True),
    sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('delivery_photo_url', sa.String(length=500), nullable=True),
    sa.Column('recipient_signature', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['recipient_id'], ['parties.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['sender_id'], ['parties.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('org_id', 'tracking_id', name='uq_org_tracking_id')
    )
    op.create_index('ix_org_orders_courier_id', 'orders', ['org_id', 'courier_id'], unique=False)
    op.create_index('ix_org_orders_status', 'orders', ['org_id', 'status'], unique=False)
    op.create_table('package_details',
    sa.Column('type', sa.Enum('BOX', 'PACKAGE', 'ENVELOPE', 'OTHER', name='package_type'), nullable=False),
    sa.Column('content_type', sa.Enum('LETTER', 'FOOD', 'GROCERY', 'ELECTRONICS', 'CLOTHING', 'OTHER', name='content_type'), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('length', sa.Float(), nullable=True),
    sa.Column('width', sa.Float(), nullable=True),
    sa.Column('height', sa.Float(), nullable=True),
    sa.Column('weight', sa.Float(), nullable=True),
    sa.Column('is_fragile', sa.Boolean(), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('org_id', 'order_id', name='uq_org_order_package_detail')
    )
    op.create_table('time_windows',
    sa.Column('day', sa.Date(), nullable=False),
    sa.Column('time_from', sa.Time(), nullable=True),
    sa.Column('time_to', sa.Time(), nullable=True),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_index('ix_org_order_time_window', 'time_windows', ['org_id', 'order_id'], unique=False)

    # Enable Row Level Security on new tables
    op.execute("ALTER TABLE parties ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE package_details ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE time_windows ENABLE ROW LEVEL SECURITY")

    # Create RLS policies for organizations
    op.execute(
        """
        CREATE POLICY org_isolation_parties ON parties
        USING (org_id = current_setting('app.org_id', true)::uuid)
    """
    )
    op.execute(
        """
        CREATE POLICY org_isolation_orders ON orders
        USING (org_id = current_setting('app.org_id', true)::uuid)
    """
    )
    op.execute(
        """
        CREATE POLICY org_isolation_package_details ON package_details
        USING (org_id = current_setting('app.org_id', true)::uuid)
    """
    )
    op.execute(
        """
        CREATE POLICY org_isolation_time_windows ON time_windows
        USING (org_id = current_setting('app.org_id', true)::uuid)
    """
    )


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS org_isolation_package_details ON package_details")
    op.execute("DROP POLICY IF EXISTS org_isolation_time_windows ON time_windows")
    op.execute("DROP POLICY IF EXISTS org_isolation_orders ON orders")
    op.execute("DROP POLICY IF EXISTS org_isolation_parties ON parties")

    # Disable RLS
    op.execute("ALTER TABLE package_details DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE time_windows DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE orders DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE parties DISABLE ROW LEVEL SECURITY")

    op.drop_index('ix_org_order_time_window', table_name='time_windows')
    op.drop_table('time_windows')
    op.drop_table('package_details')
    op.drop_index('ix_org_orders_status', table_name='orders')
    op.drop_index('ix_org_orders_courier_id', table_name='orders')
    op.drop_table('orders')
    op.drop_index('ix_org_parties_company', table_name='parties')
    op.drop_index('ix_org_parties_address', table_name='parties')
    op.drop_table('parties')
