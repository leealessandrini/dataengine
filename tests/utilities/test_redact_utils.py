import pytest
from capsulecorp.utilities import redact_utils


@pytest.mark.parametrize("test_input", [
    "00:1A:2B:3C:4D:5E",
    "00-1A-2B-3C-4D-5E",
    "a0:b1:c2:d3:e4:f5",
    "A0:B1:C2:D3:E4:F5"
])
def test_mac_regex_positive_cases(test_input):
    """Test cases that should match the MAC address regex."""
    assert redact_utils.MAC_REGEX.fullmatch(test_input) is not None


@pytest.mark.parametrize("test_input", [
    "00:1A:2B:3C:4D",
    "00-1A-2B-3C",
    "001A2B3C4D",
    "00;1A;2B;3C;4D;5E",
    "A0:B1:C2:D3:E4:G5"
])
def test_mac_regex_negative_cases(test_input):
    """Test cases that should not match the MAC address regex."""
    assert redact_utils.MAC_REGEX.fullmatch(test_input) is None
