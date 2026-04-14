import os
import tempfile
import unittest
from unittest.mock import patch

import fitz

from utils import vector_store


class FakeEmbeddings:
    """Deterministic fake embeddings for vector store lifecycle tests."""

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        payload = text.encode("utf-8")[:16]
        values = [((byte / 255.0) * 2.0) - 1.0 for byte in payload]
        values.extend([0.0] * (16 - len(values)))
        return values


class VectorStoreRebuildTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.docs_dir = os.path.join(self.tempdir.name, "docs")
        self.persist_dir = os.path.join(self.tempdir.name, "vectorstore")
        os.makedirs(self.docs_dir, exist_ok=True)
        self._create_pdf(
            "returns_policy.pdf",
            "Most unopened products can be returned within 30 days of purchase.",
        )
        self._create_pdf(
            "support_policy.pdf",
            "Premium members receive priority support and longer live-chat coverage.",
        )

    def tearDown(self):
        vector_store.invalidate_vector_store_cache()
        self.tempdir.cleanup()

    def _create_pdf(self, filename, text):
        path = os.path.join(self.docs_dir, filename)
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text)
        doc.save(path)
        doc.close()

    def test_chunk_metadata_includes_page_and_line_context(self):
        chunks = vector_store.load_and_split_pdfs(docs_dir=self.docs_dir)

        self.assertGreater(len(chunks), 0)
        first_chunk = chunks[0]
        self.assertIn("source", first_chunk.metadata)
        self.assertIn("page", first_chunk.metadata)
        self.assertIn("line_start", first_chunk.metadata)
        self.assertIn("line_end", first_chunk.metadata)
        self.assertIn("chunk_index", first_chunk.metadata)
        self.assertEqual(first_chunk.metadata["page"], 1)
        self.assertGreaterEqual(first_chunk.metadata["line_start"], 1)
        self.assertGreaterEqual(
            first_chunk.metadata["line_end"],
            first_chunk.metadata["line_start"],
        )

    @patch.object(vector_store, "OpenAIEmbeddings", return_value=FakeEmbeddings())
    def test_rebuild_clears_stale_chroma_runtime(self, _mock_embeddings):
        first_store = vector_store.build_vector_store(
            docs_dir=self.docs_dir,
            persist_dir=self.persist_dir,
        )
        first_count = first_store._collection.count()

        second_store = vector_store.build_vector_store(
            docs_dir=self.docs_dir,
            persist_dir=self.persist_dir,
        )
        second_count = second_store._collection.count()

        loaded_store = vector_store.get_vector_store(persist_dir=self.persist_dir)
        loaded_count = loaded_store._collection.count()

        self.assertGreater(first_count, 0)
        self.assertEqual(second_count, first_count)
        self.assertEqual(loaded_count, first_count)


if __name__ == "__main__":
    unittest.main()
