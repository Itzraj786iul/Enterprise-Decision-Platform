"""Authentication models, roles, and permissions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    EXECUTIVE = "executive"
    FINANCE = "finance"
    OPERATIONS = "operations"
    SALES = "sales"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    DASHBOARD_READ = "dashboard:read"
    SALES_READ = "sales:read"
    CUSTOMERS_READ = "customers:read"
    FINANCE_READ = "finance:read"
    OPERATIONS_READ = "operations:read"
    ANALYTICS_READ = "analytics:read"
    ML_READ = "ml:read"
    REPORTS_READ = "reports:read"
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"
    EXPORT = "export:run"
    ADMIN = "admin:all"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.EXECUTIVE: frozenset(
        {
            Permission.DASHBOARD_READ,
            Permission.SALES_READ,
            Permission.CUSTOMERS_READ,
            Permission.FINANCE_READ,
            Permission.OPERATIONS_READ,
            Permission.ANALYTICS_READ,
            Permission.ML_READ,
            Permission.REPORTS_READ,
            Permission.SETTINGS_READ,
            Permission.EXPORT,
        }
    ),
    Role.FINANCE: frozenset(
        {
            Permission.DASHBOARD_READ,
            Permission.FINANCE_READ,
            Permission.ANALYTICS_READ,
            Permission.REPORTS_READ,
            Permission.SETTINGS_READ,
            Permission.EXPORT,
        }
    ),
    Role.OPERATIONS: frozenset(
        {
            Permission.DASHBOARD_READ,
            Permission.OPERATIONS_READ,
            Permission.ANALYTICS_READ,
            Permission.REPORTS_READ,
            Permission.SETTINGS_READ,
            Permission.EXPORT,
        }
    ),
    Role.SALES: frozenset(
        {
            Permission.DASHBOARD_READ,
            Permission.SALES_READ,
            Permission.CUSTOMERS_READ,
            Permission.ANALYTICS_READ,
            Permission.REPORTS_READ,
            Permission.SETTINGS_READ,
            Permission.EXPORT,
        }
    ),
    Role.ANALYST: frozenset(
        {
            Permission.DASHBOARD_READ,
            Permission.SALES_READ,
            Permission.CUSTOMERS_READ,
            Permission.FINANCE_READ,
            Permission.OPERATIONS_READ,
            Permission.ANALYTICS_READ,
            Permission.ML_READ,
            Permission.REPORTS_READ,
            Permission.SETTINGS_READ,
            Permission.EXPORT,
        }
    ),
    Role.VIEWER: frozenset(
        {
            Permission.DASHBOARD_READ,
            Permission.SALES_READ,
            Permission.CUSTOMERS_READ,
            Permission.FINANCE_READ,
            Permission.OPERATIONS_READ,
            Permission.ANALYTICS_READ,
            Permission.REPORTS_READ,
            Permission.SETTINGS_READ,
        }
    ),
}


def permissions_for_roles(roles: list[str] | tuple[str, ...]) -> frozenset[Permission]:
    granted: set[Permission] = set()
    for raw in roles:
        try:
            role = Role(raw.lower())
        except ValueError:
            continue
        granted.update(ROLE_PERMISSIONS.get(role, frozenset()))
    return frozenset(granted)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None = None
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    is_authenticated: bool = False
    token_claims: dict = field(default_factory=dict, hash=False, compare=False)

    def has_permission(self, permission: Permission | str) -> bool:
        value = permission.value if isinstance(permission, Permission) else permission
        if Permission.ADMIN.value in self.permissions:
            return True
        return value in self.permissions

    def has_any_permission(self, *permissions: Permission | str) -> bool:
        return any(self.has_permission(p) for p in permissions)
