import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from src import indexer


class IndexerTests(unittest.IsolatedAsyncioTestCase):
    def test_pdf_documents_are_encoded_as_binary_content(self):
        pdf_path = Path("documents") / "1706.03762v7.pdf"
        if not pdf_path.exists():
            self.skipTest("PDF fixture is not present")

        document = indexer._parse_document_file(pdf_path)

        self.assertEqual(document["body"]["mimeType"], "application/pdf")
        self.assertIn("binaryContent", document["body"])
        self.assertNotIn("textContent", document["body"])

    async def test_index_documents_returns_error_for_connection_failure(self):
        documents = [{"id": "doc1", "title": "Doc 1"}]

        class DummyClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, *args, **kwargs):
                raise httpx.ConnectError("[Errno 11001] getaddrinfo failed")

        with patch("src.indexer.get_indexing_client", return_value=DummyClient()):
            result = await indexer.index_documents(documents)

        self.assertEqual(result["status"], "error")
        self.assertIn("connection", result["message"].lower())


if __name__ == "__main__":
    unittest.main()
