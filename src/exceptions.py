"""
Enterprise Employee Analytics - Custom Exceptions Hierarchy
============================================================
Defines domain and operational exceptions for the OOP backend,
data access layer (DAL), and ETL orchestration.

Author: Enterprise Data Architecture Team
"""


class EnterpriseAnalyticsError(Exception):
    """Base exception for all Enterprise Employee Analytics errors."""
    pass


class DatabaseError(EnterpriseAnalyticsError):
    """Raised when a database connection, transaction, or query execution fails."""
    pass


class ValidationError(ValueError, EnterpriseAnalyticsError):
    """Raised when an entity attribute fails domain validation constraints.
    Inherits from ValueError for seamless backwards compatibility.
    """
    pass


class EntityNotFoundError(ValueError, EnterpriseAnalyticsError):
    """Raised when an expected domain entity or record cannot be located.
    Inherits from ValueError for seamless backwards compatibility.
    """
    pass


class ETLError(EnterpriseAnalyticsError):
    """Raised when an ETL pipeline or data synchronization step encounters a failure."""
    pass
