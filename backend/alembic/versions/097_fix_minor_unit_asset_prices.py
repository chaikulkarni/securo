"""fix minor unit asset valuations (e.g. GBp/pence on London Stock Exchange)

Revision ID: 097
Revises: 096
Create Date: 2026-08-31
"""
from typing import Sequence, Union

from alembic import op

revision: str = "097"
down_revision: Union[str, None] = "096"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Fix assets where last_price was stored in pence / minor units
    op.execute(
        """
        UPDATE assets
        SET last_price = ROUND(last_price / 100, 6)
        WHERE valuation_method = 'market_price'
          AND last_price IS NOT NULL
          AND (
            (ticker ILIKE '%.L' OR ticker ILIKE '%.IL' OR ticker ILIKE '%.JO' OR ticker ILIKE '%.TA')
            AND (
              (average_price IS NOT NULL AND average_price > 0 AND last_price > average_price * 20)
              OR (last_price > 50 AND currency = 'GBP')
            )
          );
        """
    )

    # 2. Fix asset_values rows that recorded unnormalized minor unit prices
    op.execute(
        """
        UPDATE asset_values v
        SET price = CASE WHEN v.price IS NOT NULL THEN ROUND(v.price / 100, 6) ELSE NULL END,
            amount = CASE 
              WHEN a.units IS NOT NULL AND a.units > 0 AND v.price IS NOT NULL 
                THEN ROUND((v.price / 100) * a.units, 6)
              ELSE ROUND(v.amount / 100, 6)
            END
        FROM assets a
        WHERE v.asset_id = a.id
          AND a.valuation_method = 'market_price'
          AND (
            (a.ticker ILIKE '%.L' OR a.ticker ILIKE '%.IL' OR a.ticker ILIKE '%.JO' OR a.ticker ILIKE '%.TA')
            AND (
              (v.price IS NOT NULL AND (
                (a.average_price IS NOT NULL AND a.average_price > 0 AND v.price > a.average_price * 20)
                OR (v.price > 50 AND a.currency = 'GBP')
              ))
              OR (v.price IS NULL AND v.amount > 100000 AND a.currency = 'GBP')
            )
          );
        """
    )


def downgrade() -> None:
    pass
