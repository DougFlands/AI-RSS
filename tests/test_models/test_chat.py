import unittest
from unittest.mock import patch, MagicMock
from src.core.models.chat import AIChat

class TestAIChat(unittest.TestCase):
    def setUp(self):
        self.chat = AIChat(modelType="coze", system_prompt="Test prompt")
        
    def test_init(self):
        self.assertEqual(self.chat.modelType, "coze")
        self.assertEqual(self.chat.system_prompt, "Test prompt")
        self.assertEqual(self.chat.history, [])
        
    def test_add_history(self):
        self.chat.add_history("Hello", "Hi there")
        self.assertEqual(len(self.chat.history), 1)
        self.assertEqual(self.chat.history[0]["user"], "Hello")
        self.assertEqual(self.chat.history[0]["ai"], "Hi there")
        
    @patch('src.core.langchain.ollama.ChatManager')
    def test_ollama_generate(self, mock_chat_manager):
        # 设置模拟返回值
        mock_instance = MagicMock()
        mock_instance.chat.return_value = "Test response"
        mock_chat_manager.return_value = mock_instance
        
        result = self.chat._ollama_generate("Test input")
        
        
        self.assertTrue(result["response"], "Expected a non-empty response")
        
    @patch('cozepy.Coze')
    def test_coze_generate(self, mock_coze):
        # 设置模拟返回值
        mock_instance = MagicMock()
        mock_chat_poll = MagicMock()
        mock_chat_poll.messages = [MagicMock(content="Test response")]
        mock_chat_poll.chat.status = "completed"
        mock_instance.chat.create_and_poll.return_value = mock_chat_poll
        mock_coze.return_value = mock_instance
        
        result = self.chat._coze_generate("Test input")
        
        self.assertEqual(result["model"], "coze")