# utf_8_byte_boundary_py

Determines the number of additional bytes needed to complete a UTF-8
multi-byte sequence from a partial byte buffer.

```python
from utf_8_byte_boundary_py import bytes_needed, complete_sequence_length

chunk = b"hello \xc3"          # 'h','e','l','l','o',' ', then start of 'é'
bytes_needed(chunk)             # -> 1  (one continuation byte still missing)

partial = b"\xe2\x82"          # first two bytes of '€' (U+20AC)
bytes_needed(partial)           # -> 1
complete_sequence_length(partial)  # -> 3  (full expected length of the run)
```

## Why this exists

When a stream is read in fixed-size chunks, a multi-byte UTF-8 character
may be split across two reads.  Before passing the chunk to a strict
decoder you want to know whether the tail is complete or how many more
bytes to fetch first.  This library answers exactly that question and
nothing else — it does not validate the *content* of continuation bytes,
only counts them against the length implied by the last lead byte.

## Edge cases

- A buffer that is entirely continuation bytes (no lead byte anywhere)
  returns ``-1`` from :func:`bytes_needed`, because the sequence length
  cannot be inferred from continuations alone.  Treat this as
  "undecodable tail" rather than trying to read more bytes.
- Lead bytes ``0xF8``..``0xFF`` are outside RFC 3629's valid range
  (which caps at ``0xF4``) and likewise produce ``-1``.
- The maximum return value is ``3``, because a UTF-8 sequence is at
  most four bytes and a single lead byte has already been seen.

## Exported names

- ``bytes_needed(buf)`` — additional bytes required to finish the
  trailing sequence; ``0`` on a boundary, ``1``–``3`` when split,
  ``-1`` when undecodable.
- ``complete_sequence_length(buf)`` — the full expected length of the
  trailing sequence (``2``–``4``), or ``0`` when the buffer is on a
  boundary or the tail is undecodable.
