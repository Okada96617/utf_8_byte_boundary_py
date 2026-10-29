import unittest

from utf_8_byte_boundary_py import bytes_needed, complete_sequence_length


class TestBytesNeeded(unittest.TestCase):
    # --- boundaries and happy path ---

    def test_empty_buffer_is_boundary(self):
        self.assertEqual(bytes_needed(b""), 0)

    def test_plain_ascii_is_boundary(self):
        self.assertEqual(bytes_needed(b"hello"), 0)

    def test_complete_two_byte_sequence(self):
        # U+00A9 © — C3 A9
        self.assertEqual(bytes_needed(b"\xc3\xa9"), 0)

    def test_complete_three_byte_sequence(self):
        # U+20AC € — E2 82 AC
        self.assertEqual(bytes_needed(b"\xe2\x82\xac"), 0)

    def test_complete_four_byte_sequence(self):
        # U+1F600 — F0 9F 98 80
        self.assertEqual(bytes_needed(b"\xf0\x9f\x98\x80"), 0)

    # --- split sequences ---

    def test_two_byte_missing_one(self):
        # Lead C3 but no continuation yet.
        self.assertEqual(bytes_needed(b"\xc3"), 1)

    def test_two_byte_split_after_boundary(self):
        # ASCII text then a lone two-byte lead at the end.
        self.assertEqual(bytes_needed(b"abc\xc3"), 1)

    def test_three_byte_missing_two(self):
        self.assertEqual(bytes_needed(b"\xe2"), 2)

    def test_three_byte_missing_one(self):
        self.assertEqual(bytes_needed(b"\xe2\x82"), 1)

    def test_four_byte_missing_three(self):
        self.assertEqual(bytes_needed(b"\xf0"), 3)

    def test_four_byte_missing_two(self):
        self.assertEqual(bytes_needed(b"\xf0\x9f"), 2)

    def test_four_byte_missing_one(self):
        self.assertEqual(bytes_needed(b"\xf0\x9f\x98"), 1)

    # --- multiple sequences in one buffer ---

    def test_complete_then_split(self):
        # Complete two-byte sequence followed by a three-byte lead.
        self.assertEqual(bytes_needed(b"\xc3\xa9\xe2"), 2)

    def test_split_then_split(self):
        # Two-byte lead then (unrelated) four-byte lead at the end.
        self.assertEqual(bytes_needed(b"\xc3\xf0"), 3)

    # --- undecodable tails ---

    def test_all_continuation_bytes(self):
        # No lead byte anywhere — cannot determine sequence length.
        self.assertEqual(bytes_needed(b"\x80\x80\x80"), -1)

    def test_invalid_lead_0xf8(self):
        # 0xF8 is outside the valid lead-byte range (RFC 3629 caps at 0xF4).
        self.assertEqual(bytes_needed(b"\xf8"), -1)

    def test_invalid_lead_0xff(self):
        self.assertEqual(bytes_needed(b"\xff"), -1)

    # --- type handling ---

    def test_bytearray_accepted(self):
        self.assertEqual(bytes_needed(bytearray(b"\xc3")), 1)

    def test_none_raises_type_error(self):
        with self.assertRaises(TypeError):
            bytes_needed(None)

    def test_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            bytes_needed("hello")  # type: ignore[arg-type]


class TestCompleteSequenceLength(unittest.TestCase):

    def test_boundary_returns_zero(self):
        self.assertEqual(complete_sequence_length(b"hello"), 0)

    def test_two_byte_lead(self):
        self.assertEqual(complete_sequence_length(b"\xc3"), 2)

    def test_three_byte_lead(self):
        self.assertEqual(complete_sequence_length(b"\xe2"), 3)

    def test_three_byte_partial(self):
        self.assertEqual(complete_sequence_length(b"\xe2\x82"), 3)

    def test_four_byte_lead(self):
        self.assertEqual(complete_sequence_length(b"\xf0"), 4)

    def test_undecodable_returns_zero(self):
        self.assertEqual(complete_sequence_length(b"\x80\x80"), 0)

    def test_invalid_lead_returns_zero(self):
        self.assertEqual(complete_sequence_length(b"\xf8\x80"), 0)


if __name__ == "__main__":
    unittest.main()
