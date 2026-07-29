"""Application-level errors suitable for presentation to a caller."""


class InvalidReportInputError(ValueError):
    """Raised when a report code or URL cannot be normalized."""
