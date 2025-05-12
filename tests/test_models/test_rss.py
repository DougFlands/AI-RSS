import unittest
from unittest.mock import patch, MagicMock
from src.core.models.rss import ParseRss, OutputRss
from src.core.models.email import SendEmail

class TestRss(unittest.TestCase):
    def setUp(self):
        self.sample_feed = {
            'entries': [
                {
                    'title': 'Test Title',
                    'link': 'http://test.com',
                    'published': '2024-01-01',
                    'summary': 'Test Summary'
                }
            ]
        }

    @patch('src.core.models.rss.ParseRss')
    def test_output_rss(self, mock_parse_rss, mock_get_config):
        # 设置模拟数据
        mock_get_config.return_value = ['http://test1.com/feed', 'http://test2.com/feed']
        mock_parse_rss.return_value = [self.sample_feed['entries'][0]]
        
        result = OutputRss()
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertIn('http://test1.com/feed', result)
        self.assertIn('http://test2.com/feed', result)

