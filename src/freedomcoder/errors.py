class FreedomCoderError(Exception):
    """Base exception for user-facing FreedomCoder failures."""


class ConfigurationError(FreedomCoderError):
    """Raised when project configuration is invalid."""


class ProfileError(FreedomCoderError):
    """Raised when a built-in model profile cannot be resolved."""


class RuntimeIntegrationError(FreedomCoderError):
    """Raised when a local runtime integration fails."""
