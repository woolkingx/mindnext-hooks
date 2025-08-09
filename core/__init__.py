"""
MindNext Hooks - Core System Services
====================================

Core layer provides fundamental system services:
- Buffer: Event buffering and queuing system
- Cache: High-performance caching with LRU and TTL
- File Monitor: Configuration change detection

Architecture:
Core Layer (System Services) → Action Layer (Interface) → Rule Layer (Logic)
"""

from .buffer import CoreBuffer
from .cache import CoreCache

__all__ = ['CoreBuffer', 'CoreCache']