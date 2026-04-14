import unittest

from app import _split_message_and_sources


class AppMessageRenderingTests(unittest.TestCase):
    def test_split_message_handles_bold_source_footer(self):
        answer, sources = _split_message_and_sources(
            "Answer body\n\n---\n**Source:** `customers`\n**SQL:** `SELECT 1`"
        )
        self.assertEqual(answer, "Answer body")
        self.assertEqual(sources, "**Source:** `customers`\n**SQL:** `SELECT 1`")

    def test_split_message_handles_plain_source_details_footer(self):
        answer, sources = _split_message_and_sources(
            "Hybrid answer\n\n---\n\nSource Details:\n- Customer Records: row"
        )
        self.assertEqual(answer, "Hybrid answer")
        self.assertEqual(sources, "Source Details:\n- Customer Records: row")


if __name__ == "__main__":
    unittest.main()
