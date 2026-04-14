import unittest

from langchain_core.documents import Document

from agents.rag_agent import _select_relevant_docs


class RagAgentFilteringTests(unittest.TestCase):
    def test_unique_upload_terms_push_irrelevant_docs_out(self):
        question = "How quickly are BeaconShield Plus express replacement requests reviewed?"
        docs = [
            Document(
                page_content=(
                    "BeaconShield Plus extends coverage to 24 months and adds one "
                    "express replacement claim every rolling 12-month period. "
                    "Express replacement requests for BeaconShield Plus are reviewed "
                    "within 2 business hours."
                ),
                metadata={"source": "beaconshield_device_protection_policy.pdf"},
            ),
            Document(
                page_content=(
                    "Pacific Sales Outlet, Magnolia Design Center, Best Buy Education, "
                    "Best Buy Business and Best Buy Express kiosks."
                ),
                metadata={"source": "bestbuy_return_exchange_policy.pdf"},
            ),
            Document(
                page_content="Our Agents are available 24 hours a day, 7 days a week.",
                metadata={"source": "bestbuy_return_exchange_policy.pdf"},
            ),
        ]

        selected = _select_relevant_docs(question, docs)

        self.assertEqual(len(selected), 1)
        self.assertEqual(
            selected[0].metadata["source"],
            "beaconshield_device_protection_policy.pdf",
        )

    def test_falls_back_to_original_docs_when_no_terms_overlap(self):
        question = "Hello there"
        docs = [
            Document(page_content="General support info", metadata={"source": "a.pdf"}),
            Document(page_content="Another policy block", metadata={"source": "b.pdf"}),
        ]

        selected = _select_relevant_docs(question, docs)

        self.assertEqual(selected, docs)


if __name__ == "__main__":
    unittest.main()
