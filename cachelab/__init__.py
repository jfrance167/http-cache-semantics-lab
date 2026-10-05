"""Offline normalized cache reasoning; no HTTP transport or content release."""

from .contracts import Invalid, parse
from .model import evaluate

__all__ = ["Invalid", "parse", "evaluate"]
