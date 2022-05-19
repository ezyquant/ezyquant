from ezyquant import SETSignalCreator


class TestSymbolList:
    def test_one_symbol_list(self, ssc: SETSignalCreator):
        # Mock
        ssc._symbol_list = ["COM7"]

        # Test
        result = ssc.symbol_list

        # Check
        assert result == ["COM7"]
