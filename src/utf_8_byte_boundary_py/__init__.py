"""utf_8_byte_boundary_py
======================

Determines the number of additional bytes needed to complete a UTF-8
multi-byte sequence from a partial byte buffer.
"""

from .core import bytes_needed, complete_sequence_length

__all__ = ["bytes_needed", "complete_sequence_length"]
