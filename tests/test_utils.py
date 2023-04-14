import unittest
from unittest import mock

from common.utils import *


class UtilsTestCase(unittest.TestCase):

    def test_df_to_csv_whenRaiseException_thenReturnFalse(self):
        df = mock.Mock()
        self.assertEqual(df_to_csv(df), False)

    def test_sina_response_text_parser(self):
        text = 'var hq_str_bj836826="盖世食品,8.320,8.290,8.250,8.320,8.210,8.210,8.250,32277,265894.070,867,8.210,3463,8.200,500,8.190,9611,8.160,614,8.150,5718,8.250,1720,8.290,58209,8.300,2100,8.320,4740,8.340,2023-04-13,15:30:11,00,18.9312,0.0000,0,10065940,B,T";'
        result = parse_sina_response_text(text)
        self.assertEqual(result.code, "bj836826")

    def test_sina_response_text_parser_whenRaiseException_thenReturnFalse(self):
        result = parse_sina_response_text("bad string")
        empty_string = parse_sina_response_text("")
        self.assertIsNone(result)
        self.assertIsNone(empty_string)

    def test_is_bad_stock(self):
        self.assertTrue(is_bad_stock("皇叔集团退"))
        self.assertTrue(is_bad_stock("ST皇叔"))
        self.assertTrue(is_bad_stock("N皇叔"))
        self.assertFalse(is_bad_stock("皇叔股份"))

    def test_code_with_prefix(self):
        self.assertEqual(code_with_prefix("600345"), "sh600345")
        self.assertEqual(code_with_prefix("800345"), "bj800345")
        self.assertEqual(code_with_prefix("345"), "sz000345")

    def test_is_trade_time(self):
        _date1 = datetime.strptime("2023-04-15 09:50:55", "%Y-%m-%d %H:%M:%S")
        _date2 = datetime.strptime("2023-04-14 09:00:55", "%Y-%m-%d %H:%M:%S")
        _date3 = datetime.strptime("2023-04-14 09:50:55", "%Y-%m-%d %H:%M:%S")
        self.assertFalse(is_trade_time(_date1))
        self.assertFalse(is_trade_time(_date2))
        self.assertTrue(is_trade_time(_date3))


if __name__ == '__main__':
    unittest.main()
