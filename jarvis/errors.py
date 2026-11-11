"""Typed errors used across JARVIS."""

from __future__ import annotations


class JarvisError(Exception):
    """Base class for every error raised by JARVIS."""


class ConfigError(JarvisError):
    """The configuration file or an environment variable is invalid."""


class ValidationError(JarvisError):
    """User supplied input failed validation."""


class UnsafeInputError(ValidationError):
    """Input was rejected because it could harm the user or the machine."""


class NotFoundError(JarvisError):
    """The requested file, note, reminder or app does not exist."""


class FeatureUnavailable(JarvisError):
    """An optional feature is not available on this system."""


class NotSupportedError(FeatureUnavailable):
    """The feature is not supported on the current operating system."""


class IntegrationError(JarvisError):
    """A third-party integration (Gmail, WhatsApp, Twilio) failed."""


class AuthenticationError(IntegrationError):
    """Credentials are missing or were rejected."""


class NetworkError(IntegrationError):
    """A network call failed or the machine is offline."""
