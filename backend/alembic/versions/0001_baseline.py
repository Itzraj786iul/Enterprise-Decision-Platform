"""Baseline Alembic revision — platform metadata only (no business schema).

Analytics views/tables are provisioned externally (Neon + in-repo SQL under
`database/` and `sql/`). This revision ensures `alembic upgrade head`
succeeds and creates alembic_version for future ORM migrations.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Intentionally empty: no application tables yet.
    # Keep this no-op so production migrate jobs are safe.
    op.execute("SELECT 1")


def downgrade() -> None:
    pass
