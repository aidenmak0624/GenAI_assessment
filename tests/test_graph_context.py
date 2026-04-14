import unittest
from unittest.mock import ANY, MagicMock, patch

from agents import graph


class GraphContextTests(unittest.TestCase):
    def test_keyword_route_prefers_sql_for_profile_and_ticket_queries(self):
        route = graph._keyword_route(
            "Give me a quick overview of customer Ema Johnson's profile and past support ticket details."
        )
        self.assertEqual(route, "sql")

    def test_keyword_route_prefers_rag_for_policy_queries(self):
        route = graph._keyword_route(
            "What does the BeaconShield policy cover?"
        )
        self.assertEqual(route, "rag")

    def test_keyword_route_keeps_generic_return_policy_summary_on_rag(self):
        route = graph._keyword_route(
            "Summarize Best Buy's return policy for most products."
        )
        self.assertEqual(route, "rag")

    def test_keyword_route_prefers_hybrid_when_customer_and_policy_terms_mix(self):
        route = graph._keyword_route(
            "Based on Best Buy's return policy, would Ema still qualify for a refund on her SmartDesk Hub?"
        )
        self.assertEqual(route, "hybrid")

    @patch.object(graph, "answer_sql_question", return_value="SQL result")
    @patch.object(graph, "_rewrite_question_with_history", return_value="Standalone customer question")
    def test_sql_node_uses_standalone_rewrite(
        self,
        mock_rewrite,
        mock_answer_sql_question,
    ):
        state = {
            "question": "What about her tickets?",
            "chat_history": [{"role": "user", "content": "Tell me about Ema Johnson."}],
            "route": "sql",
            "sql_response": "",
            "rag_response": "",
            "response": "",
        }

        result = graph.sql_node(state, llm=object())

        mock_rewrite.assert_called_once_with(state["question"], state["chat_history"], ANY)
        mock_answer_sql_question.assert_called_once_with("Standalone customer question", ANY)
        self.assertEqual(result["sql_response"], "SQL result")

    @patch.object(graph, "answer_rag_question", return_value="RAG result")
    @patch.object(graph, "_rewrite_question_with_history", return_value="Standalone policy question")
    def test_rag_node_uses_standalone_rewrite(
        self,
        mock_rewrite,
        mock_answer_rag_question,
    ):
        state = {
            "question": "What does it say about retention?",
            "chat_history": [{"role": "user", "content": "What does Apple's privacy policy say?"}],
            "route": "rag",
            "sql_response": "",
            "rag_response": "",
            "response": "",
        }

        result = graph.rag_node(state, llm=object())

        mock_rewrite.assert_called_once_with(state["question"], state["chat_history"], ANY)
        mock_answer_rag_question.assert_called_once_with("Standalone policy question", ANY)
        self.assertEqual(result["rag_response"], "RAG result")

    @patch.object(graph, "answer_sql_facts_question", return_value="**Database Facts:**")
    @patch.object(graph, "_rewrite_question_with_history", return_value="Standalone hybrid question")
    def test_hybrid_sql_node_uses_standalone_rewrite(
        self,
        mock_rewrite,
        mock_answer_sql_facts_question,
    ):
        state = {
            "question": "Would she qualify for a refund?",
            "chat_history": [{"role": "user", "content": "Tell me about Ema's SmartDesk Hub order."}],
            "route": "hybrid",
            "sql_response": "",
            "rag_response": "",
            "response": "",
        }

        result = graph.hybrid_sql_node(state, llm=object())

        mock_rewrite.assert_called_once_with(state["question"], state["chat_history"], ANY)
        mock_answer_sql_facts_question.assert_called_once_with(
            "Standalone hybrid question",
            ANY,
        )
        self.assertEqual(result["sql_response"], "**Database Facts:**")

    @patch.object(graph, "answer_rag_question", return_value="Policy result")
    @patch.object(
        graph,
        "_rewrite_hybrid_policy_question",
        return_value="What is Best Buy's return window for most products?",
    )
    @patch.object(graph, "_rewrite_question_with_history", return_value="Standalone hybrid question")
    def test_hybrid_rag_node_rewrites_follow_up_before_policy_lookup(
        self,
        mock_rewrite_question,
        mock_rewrite_policy,
        mock_answer_rag_question,
    ):
        state = {
            "question": "Would she qualify for a refund?",
            "chat_history": [{"role": "user", "content": "Tell me about Ema's SmartDesk Hub order."}],
            "route": "hybrid",
            "sql_response": "",
            "rag_response": "",
            "response": "",
        }

        result = graph.hybrid_rag_node(state, llm=object())

        mock_rewrite_question.assert_called_once_with(state["question"], state["chat_history"], ANY)
        mock_rewrite_policy.assert_called_once_with("Standalone hybrid question", ANY)
        mock_answer_rag_question.assert_called_once_with(
            "What is Best Buy's return window for most products?",
            ANY,
        )
        self.assertEqual(result["rag_response"], "Policy result")

    def test_rewrite_question_returns_original_when_no_history(self):
        llm = MagicMock()
        rewritten = graph._rewrite_question_with_history("Standalone already", [], llm)
        self.assertEqual(rewritten, "Standalone already")
        llm.invoke.assert_not_called()

    def test_rewrite_question_skips_standalone_query_even_with_history(self):
        llm = MagicMock()
        rewritten = graph._rewrite_question_with_history(
            "How many Premium tier customers do we have?",
            [{"role": "user", "content": "Summarize Best Buy's return policy."}],
            llm,
        )
        self.assertEqual(rewritten, "How many Premium tier customers do we have?")
        llm.invoke.assert_not_called()

    def test_rewrite_question_uses_history_for_pronoun_follow_up(self):
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content="Would Ema still qualify for a refund?")
        rewritten = graph._rewrite_question_with_history(
            "Would she still qualify?",
            [{"role": "user", "content": "Tell me about Ema's order."}],
            llm,
        )
        self.assertEqual(rewritten, "Would Ema still qualify for a refund?")
        llm.invoke.assert_called_once()


if __name__ == "__main__":
    unittest.main()
