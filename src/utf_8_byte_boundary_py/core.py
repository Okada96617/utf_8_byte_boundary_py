"""Core implementation of the UTF-8 byte boundary detector.

A UTF-8 character is encoded as 1 to 4 bytes.  The first byte carries a
prefix that tells a decoder how many continuation bytes follow.  When
reading a stream in fixed-size chunks it is common to split a multi-byte
sequence across two reads; this module answers the question
"how many bytes remain to complete the sequence at the tail of this
buffer?"
"""

from __future__ import annotations


def _lead_total_length(lead: int) -> int:
    """Return the total byte-length of the sequence whose lead byte is *lead*.

    Returns ``0`` if *lead* is a continuation byte (no lead byte at this
    position) and ``1`` for an ASCII byte.
    """
    # 0xxxxxxx — ASCII single byte.
    if lead < 0x80:
        return 1
    # 10xxxxxx — a continuation byte, not a lead.
    if lead < 0xC0:
        return 0
    # 110xxxxx — two-byte sequence.
    if lead < 0xE0:
        return 2
    # 1110xxxx — three-byte sequence.
    if lead < 0xF0:
        return 3
    # 11110xxx — four-byte sequence.
    if lead < 0xF8:
        return 4
    # 0xF8..0xFF are invalid per RFC 3629 (sequences were historically
    # defined up to 6 bytes but the spec restricted the range to 4).
    return 0


def bytes_needed(buf) -> int:
    """Number of additional bytes required to finish the trailing sequence.

    ``buf`` is a ``bytes`` (or ``bytearray``) object received so far.
    The function walks backwards from the end, finds the last lead byte,
    and returns ``total_length - bytes_already_seen`` for that sequence.

    * ``0``        — the buffer ends on a complete sequence boundary.
    * ``1``–``3``  — that many continuation bytes are still missing.
    * ``-1``       — the buffer is entirely continuation bytes with no lead
      byte anywhere; the caller cannot know the sequence length and should
      treat it as undecodable.

    The return is at most ``3`` because a UTF-8 sequence is at most four
    bytes and a single lead byte has already been received.
    """
    if buf is None:
        raise TypeError("buf must not be None")
    if not isinstance(buf, (bytes, bytearray)):
        raise TypeError("buf must be bytes or bytearray")

    # An empty buffer is, by definition, on a boundary.
    if len(buf) == 0:
        return 0

    # Walk backwards over trailing continuation bytes (10xxxxxx).
    n = len(buf)
    i = n - 1
    while i >= 0 and 0x80 <= buf[i] < 0xC0:
        i -= 1

    if i < 0:
        # The entire buffer is continuation bytes with no lead byte —
        # we cannot tell how long the sequence is supposed to be.
        return -1

    total = _lead_total_length(buf[i])
    if total == 0:
        # The byte at position i is itself invalid (0xF8..0xFF) and
        # therefore does not start a well-formed sequence.  Treat the
        # tail as undecodable.
        return -1

    remaining = total - (n - i)
    # By construction remaining is in [1, total-1] when the sequence is
    # genuinely split, or <= 0 when it is already complete.  A negative
    # or zero result means the sequence is finished.
    return remaining if remaining > 0 else 0


def complete_sequence_length(buf) -> int:
    """Return the expected total length of the trailing sequence, or ``0``.

    Unlike :func:`bytes_needed` this always returns the *full* length of
    the sequence that starts at the last lead byte, regardless of how many
    bytes have already arrived.  It returns ``0`` when the buffer ends on
    a boundary or when the trailing bytes are undecodable.
    """
    need = bytes_needed(buf)
    if need <= 0:
        return 0

    n = len(buf)
    i = n - 1
    while i >= 0 and 0x80 <= buf[i] < 0xC0:
        i -= 1

    # bytes_needed already validated i >= 0 and buf[i] is a real lead.
    return _lead_total_length(buf[i])
