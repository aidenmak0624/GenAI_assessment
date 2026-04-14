import unittest
from unittest.mock import patch

from mcp_server import server


class McpServerTests(unittest.TestCase):
    @patch.object(server, "_get_llm", return_value=object())
    @patch.object(server, "answer_sql_question")
    def test_query_customer_data_delegates_to_sql_agent(
        self,
        mock_answer_sql_question,
        mock_get_llm,
    ):
        mock_answer_sql_question.return_value = "There are 11 Premium tier customers."

        result = server.query_customer_data("How many Premium tier customers do we have?")

        mock_answer_sql_question.assert_called_once_with(
            "How many Premium tier customers do we have?",
            mock_get_llm.return_value,
        )
        self.assertEqual(result, "There are 11 Premium tier customers.")

    @patch.object(server, "_get_llm", return_value=object())
    @patch.object(server, "answer_rag_question")
    def test_search_policies_delegates_to_rag_agent(
        self,
        mock_answer_rag_question,
        mock_get_llm,
    ):
        mock_answer_rag_question.return_value = (
            "BeaconShield Plus express replacement requests are reviewed within 2 business hours."
        )

        result = server.search_policies(
            "How quickly are BeaconShield Plus express replacement requests reviewed?"
        )

        mock_answer_rag_question.assert_called_once_with(
            "How quickly are BeaconShield Plus express replacement requests reviewed?",
            mock_get_llm.return_value,
        )
        self.assertIn("2 business hours", result)

    @patch.object(server, "_get_llm", return_value=object())
    @patch.object(server, "ask")
    def test_customer_support_chat_parses_chat_history(
        self,
        mock_ask,
        mock_get_llm,
    ):
        mock_ask.return_value = {
            "response": "Ema is Premium and has two open tickets.",
            "route": "hybrid",
        }
        chat_history = (
            "User: Tell me about Ema Johnson\n"
            "Assistant: Ema is a Premium customer.\n"
            "User: What about her tickets?\n"
            "Assistant: She has two open support tickets."
        )

        result = server.customer_support_chat(
            "Would her support tier affect response time?",
            chat_history=chat_history,
        )

        mock_ask.assert_called_once_with(
            "Would her support tier affect response time?",
            mock_get_llm.return_value,
            chat_history=[
                {"role": "user", "content": "Tell me about Ema Johnson"},
                {"role": "assistant", "content": "Ema is a Premium customer."},
                {"role": "user", "content": "What about her tickets?"},
                {"role": "assistant", "content": "She has two open support tickets."},
            ],
        )
        self.assertEqual(result, "Ema is Premium and has two open tickets.")


if __name__ == "__main__":
    unittest.main()
