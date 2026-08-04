"""Permission / RBAC unit tests."""

from __future__ import annotations

from app.auth.models import Permission, Role, permissions_for_roles


def test_admin_has_all_permissions() -> None:
    perms = permissions_for_roles([Role.ADMIN.value])
    assert Permission.ADMIN in perms
    assert Permission.FINANCE_READ in perms
    assert Permission.SETTINGS_WRITE in perms


def test_finance_role_cannot_read_sales() -> None:
    perms = permissions_for_roles([Role.FINANCE.value])
    assert Permission.FINANCE_READ in perms
    assert Permission.SALES_READ not in perms


def test_sales_role_can_read_customers() -> None:
    perms = permissions_for_roles([Role.SALES.value])
    assert Permission.SALES_READ in perms
    assert Permission.CUSTOMERS_READ in perms
    assert Permission.OPERATIONS_READ not in perms


def test_viewer_is_read_only() -> None:
    perms = permissions_for_roles([Role.VIEWER.value])
    assert Permission.EXPORT not in perms
    assert Permission.SETTINGS_WRITE not in perms
    assert Permission.DASHBOARD_READ in perms


def test_multi_role_union() -> None:
    perms = permissions_for_roles([Role.FINANCE.value, Role.SALES.value])
    assert Permission.FINANCE_READ in perms
    assert Permission.SALES_READ in perms


def test_unknown_role_ignored() -> None:
    perms = permissions_for_roles(["not-a-role"])
    assert perms == frozenset()
