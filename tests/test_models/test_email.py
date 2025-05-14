import unittest
from unittest.mock import patch, MagicMock
from src.core.models.rss import ParseRss, OutputRss
from src.core.models.email import SendEmail

class TestEmail(unittest.TestCase):
    @patch('app.extensions.mail.send')
    @patch('src.core.utils.config.get_env_variable')
    def test_send_email_success(self, mock_get_env, mock_send):
        # 设置模拟数据
        mock_get_env.return_value = 'test@example.com'
        
        # 调用函数
        result = SendEmail(
            subject='Test Subject',
            recipients=['recipient@example.com'],
            html='<p>Test Content</p>'
        )
        
        # 验证结果
        self.assertEqual(result, '邮件发送成功！')
        mock_send.assert_called_once()
        
    @patch('app.extensions.mail.send')
    def test_send_email_failure(self, mock_send):
        # 模拟发送失败
        mock_send.side_effect = Exception('Send failed')
        
        # 调用函数
        result = SendEmail(
            subject='Test Subject',
            recipients=['recipient@example.com'],
            html='<p>Test Content</p>'
        )
        
        # 验证结果
        self.assertTrue(result.startswith('邮件发送失败：')) 