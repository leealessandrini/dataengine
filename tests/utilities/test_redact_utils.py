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


def test_find_unique_macs_no_macs():
    assert redact_utils.find_unique_macs("No MAC addresses here!") == []


def test_find_unique_macs_single_mac():
    assert redact_utils.find_unique_macs(
        "Here's a MAC address: 00:1A:2B:3C:4D:5E") == ["00:1A:2B:3C:4D:5E"]


def test_find_unique_macs_multiple_unique_macs():
    assert redact_utils.find_unique_macs(
        "Two MACs: 00:1A:2B:3C:4D:5E and AA:BB:CC:DD:EE:FF"
    ) == ["00:1A:2B:3C:4D:5E", "AA:BB:CC:DD:EE:FF"]


def test_find_unique_macs_duplicate_macs():
    assert redact_utils.find_unique_macs(
        "Duplicate MACs: 00:1A:2B:3C:4D:5E and 00:1A:2B:3C:4D:5E"
    ) == ["00:1A:2B:3C:4D:5E"]


def test_find_unique_macs_case_sensitivity():
    assert redact_utils.find_unique_macs(
        "Case Test: 00:1a:2b:3c:4d:5e", case="upper") == ["00:1A:2B:3C:4D:5E"]
    assert redact_utils.find_unique_macs(
        "Case Test: 00:1A:2B:3C:4D:5E", case="lower") == ["00:1a:2b:3c:4d:5e"]


def test_find_unique_macs_mixed_case():
    assert redact_utils.find_unique_macs(
        "Mixed Case: 00:1a:2B:3C:4d:5E and 00:1A:2b:3c:4D:5e", case="upper"
    ) == ["00:1A:2B:3C:4D:5E"]
    assert redact_utils.find_unique_macs(
        "Mixed Case: 00:1a:2B:3C:4d:5E and 00:1A:2b:3c:4D:5e", case="lower"
    ) == ["00:1a:2b:3c:4d:5e"]


def test_generate_random_mac_type():
    mac = redact_utils.generate_random_mac()
    assert isinstance(mac, str)


def test_generate_random_mac_format():
    mac = redact_utils.generate_random_mac()
    assert bool(redact_utils.MAC_REGEX.match(mac))


def test_generate_random_mac_uniqueness():
    macs = {redact_utils.generate_random_mac() for _ in range(100)}
    assert len(macs) == 100


def test_redact_macs_from_text_no_macs():
    text, mac_map = redact_utils.redact_macs_from_text(
        "No MAC addresses here!")
    assert text == "No MAC addresses here!"
    assert mac_map == {}


def test_redact_macs_from_text_single_mac():
    text, mac_map = redact_utils.redact_macs_from_text(
        "Here's a MAC address: 00:1A:2B:3C:4D:5E")
    assert len(mac_map) == 1
    assert "00:1A:2B:3C:4D:5E" in mac_map
    assert redact_utils.find_unique_macs(text) == [
        mac_map["00:1A:2B:3C:4D:5E"]]


def test_redact_macs_from_text_multiple_macs():
    text, mac_map = redact_utils.redact_macs_from_text(
        "Two MACs: 00:1A:2B:3C:4D:5E and AA:BB:CC:DD:EE:FF")
    assert len(mac_map) == 2
    assert "00:1A:2B:3C:4D:5E" in mac_map
    assert "AA:BB:CC:DD:EE:FF" in mac_map
    redacted_mac_list = list(mac_map.values())
    redacted_mac_list.sort()
    assert redact_utils.find_unique_macs(text) == redacted_mac_list


def test_redact_macs_from_text_existing_mac_map():
    existing_map = {"00:1A:2B:3C:4D:5E": "FF:FF:FF:FF:FF:FF"}
    text, mac_map = redact_utils.redact_macs_from_text(
        "Here's a MAC address: 00:1A:2B:3C:4D:5E", mac_map=existing_map)
    assert mac_map == existing_map
    assert redact_utils.find_unique_macs(text) == [
        mac_map["00:1A:2B:3C:4D:5E"]]


def test_redact_macs_from_text_case_sensitivity():
    text, mac_map = redact_utils.redact_macs_from_text(
        "Case Test: 00:1a:2b:3c:4d:5e", case="upper")
    assert "00:1A:2B:3C:4D:5E" in mac_map
    assert all(mac == mac.upper() for mac in mac_map.keys())
    assert redact_utils.find_unique_macs(text) == [
        mac_map["00:1A:2B:3C:4D:5E"]]
