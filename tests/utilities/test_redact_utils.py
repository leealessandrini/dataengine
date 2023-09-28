import re
import pytest
from dataengine.utilities import redact_utils


@pytest.mark.parametrize("test_input", [
    "00:1A:2B:3C:4D:5E",
    "00-1A-2B-3C-4D-5E",
    "a0:b1:c2:d3:e4:f5",
    "A0:B1:C2:D3:E4:F5",
    "A0B1C2D3E4F5"
])
def test_mac_regex_positive_cases(test_input):
    """Test cases that should match the MAC address regex."""
    assert redact_utils.MAC_REGEX.fullmatch(test_input) is not None


@pytest.mark.parametrize("test_input", [
    "00:1A:2B:3C:4D",
    "00-1A-2B-3C",
    "001A2B3C4D",
    "00;1A;2B;3C;4D;5E",
    "A0:B1:C2:D3:E4:G5",
    "A0:B1-C2:D3:E4-F5",
    "20230718-0426",
    "1234567890123"
])
def test_mac_regex_negative_cases(test_input):
    """Test cases that should not match the MAC address regex."""
    assert redact_utils.MAC_REGEX.fullmatch(test_input) is None


@pytest.mark.parametrize("mac_address,expected", [
    # Test with a generated local MAC address
    (redact_utils.generate_random_local_mac(), True),
    # Test with a known local MAC address
    ("01:23:45:67:89:AB", True),
    # Test with a known non-local MAC address
    ("00:23:45:67:89:AB", False),
])
def test_local_mac_regex(mac_address, expected):
    # Check if the MAC address matches the regex
    if expected:
        assert (
            redact_utils.LOCAL_MAC_REGEX.fullmatch(mac_address) is not None,
            f"MAC address {mac_address} did not match the regex")
    else:
        assert (
            redact_utils.LOCAL_MAC_REGEX.fullmatch(mac_address) is None,
            f"MAC address {mac_address} incorrectly matched the regex")


def test_add_colons_to_mac():
    # Test with valid MAC addresses without separators
    mac_without_separator = "0123456789AB"
    mac_with_colon = redact_utils.add_colons_to_mac(mac_without_separator)
    # Check if colons have been added correctly
    assert (
        mac_with_colon == "01:23:45:67:89:AB",
        "Failed to correctly add colons")
    # Check if the format is correct using regex
    assert re.fullmatch(
        r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}",
        mac_with_colon) is not None, "Invalid MAC address format"
    # Test with an invalid MAC address (length not equal to 12)
    invalid_mac = "0123456789A"
    try:
        redact_utils.add_colons_to_mac(invalid_mac)
    except ValueError as e:
        assert (
            str(e) == "Invalid MAC address length",
            "Did not raise correct exception for invalid MAC address")


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


def test_find_unique_macs_duplicate_macs_no_colons():
    assert redact_utils.find_unique_macs(
        "Duplicate MACs: 00:1A:2B:3C:4D:5E and 001A2B3C4D5E"
    ) == ["00:1A:2B:3C:4D:5E"]


def test_find_mac_in_filename():
    assert redact_utils.find_unique_macs(
        "The filename is 001A2B3C4D5E_something.tgz"
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


def test_find_unique_macs_mixed_separator():
    assert redact_utils.find_unique_macs(
        "00:1a:2B:3C:4d:5E and 00-1a-2B-3C-4d-5E and 001a2B3C4d5E",
        case="upper"
    ) == ["00:1A:2B:3C:4D:5E"]


def test_generate_random_mac_type():
    mac = redact_utils.generate_random_mac()
    assert isinstance(mac, str)


def test_generate_random_mac_format():
    mac = redact_utils.generate_random_mac()
    assert bool(redact_utils.MAC_REGEX.match(mac))


def test_generate_random_mac_uniqueness():
    macs = {redact_utils.generate_random_mac() for _ in range(100)}
    assert len(macs) == 100


def test_generate_random_local_mac():
    local_mac_sum = sum([
        True if redact_utils.LOCAL_MAC_REGEX.fullmatch(
            redact_utils.generate_random_local_mac()
        ) else False
        for _ in range(100)])
    assert local_mac_sum == 100


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


def test_redact_macs_from_text_local_mac():
    original_text = "Here's a MAC address: 02:23:45:67:89:AB"
    text, mac_map = redact_utils.redact_macs_from_text(original_text)
    assert text == original_text
    assert mac_map == {"02:23:45:67:89:AB": "02:23:45:67:89:AB"}


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

@pytest.mark.parametrize('test_input,expected', [
    ('192.168.1.1', ['192.168.1.1']),
    ('0.0.0.0', ['0.0.0.0']),
    ('255.255.255.255', ['255.255.255.255']),
    ('>192.168.1.1<', ["192.168.1.1"]),
    ('The IP is 10.0.0.2.', ['10.0.0.2']),
    ('Two IPs: 192.168.0.1, 172.16.0.2', ['192.168.0.1', '172.16.0.2']),
])
def test_valid_ipv4(test_input, expected):
    assert redact_utils.IPv4_REGEX.findall(test_input) == expected


@pytest.mark.parametrize('test_input,expected', [
    ('192.168.1.256', []),
    ('192.168.1', []),
    ('192.168.1.300', []),
    ('.192.168.1.1', []),
    ('a192.168.1.1', []),
])
def test_invalid_ipv4(test_input, expected):
    assert redact_utils.IPv4_REGEX.findall(test_input) == expected


@pytest.mark.parametrize('test_input,expected', [
    ('192.168.1.1', ['192.168.1.1']),
    ('0.0.0.0', ['0.0.0.0']),
    ('255.255.255.255', ['255.255.255.255']),
    ('The IP is 10.0.0.2.', ['10.0.0.2']),
    ('Two IPs: 192.168.0.1, 172.16.0.2', ['172.16.0.2', '192.168.0.1']),
    ('No IPs here!', []),
    ('.192.168.1.1', []),
    ('192.168.1.300', []),
    ('', []),
])
def test_find_unique_ipv4(test_input, expected):
    assert redact_utils.find_unique_ipv4(test_input) == expected


@pytest.mark.parametrize('test_input,expected', [
    ('2001:0db8:85a3:0000:0000:8a2e:0370:7334', ['2001:0db8:85a3:0000:0000:8a2e:0370:7334']),
    ('::1', ['::1']),
    ('::', ['::']),
    ('The IPv6 is 2001:0db8:85a3:0000:0000:8a2e:0370:7334.', ['2001:0db8:85a3:0000:0000:8a2e:0370:7334']),
    ('Two IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334, fe80::202:b3ff:fe1e:8329', 
     ['2001:0db8:85a3:0000:0000:8a2e:0370:7334', 'fe80::202:b3ff:fe1e:8329']),
    ('No IPs here!', []),
    ('.2001:0db8:85a3:0000:0000:8a2e:0370:7334', []),
    ('2001:0db8:85a3:0000:0000:8a2e:0370:xyz', []),
    ('', []),
])
def test_ipv6_regex(test_input, expected):
    ipv6_addresses = [
        match[0] for match in redact_utils.IPv6_REGEX.findall(test_input)]
    assert ipv6_addresses == expected


@pytest.mark.parametrize("test_input,case,expected", [
    (
        'Two IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334, ::1', None,
        ['2001:0db8:85a3:0000:0000:8a2e:0370:7334', '::1']),
    ('Another IPv6: ::', None, ['::']),
    (
        'IPv6 with different cases: 2001:0db8::ff00:42:8329 and 2001:0DB8::FF00:42:8329',
        'lower', ['2001:0db8::ff00:42:8329']),
    (
        'IPv6 with different cases: 2001:0db8::ff00:42:8329 and 2001:0DB8::FF00:42:8329',
        'upper', ['2001:0DB8::FF00:42:8329']),
    ('No IPv6 here!', None, [])
])
def test_find_unique_ipv6_parametrized(test_input, case, expected):
    result = redact_utils.find_unique_ipv6(test_input, case=case)
    assert result == expected, f"For {test_input}, expected {expected} but got {result}"


def test_generate_random_ipv4_type():
    ipv4 = redact_utils.generate_random_ipv4()
    assert isinstance(ipv4, str)


def test_generate_random_ipv4_format():
    ipv4 = redact_utils.generate_random_ipv4()
    assert bool(redact_utils.IPv4_REGEX.match(ipv4))


def test_generate_random_ipv4_uniqueness():
    ipv4_addresses = {redact_utils.generate_random_ipv4() for _ in range(100)}
    assert len(ipv4_addresses) == 100


def test_generate_random_ipv6_type():
    ipv6 = redact_utils.generate_random_ipv6()
    assert isinstance(ipv6, str)


def test_generate_random_ipv6_format():
    ipv6 = redact_utils.generate_random_ipv6()
    assert bool(redact_utils.IPv6_REGEX.match(ipv6))


def test_generate_random_ipv6_uniqueness():
    ipv6_addresses = {redact_utils.generate_random_ipv6() for _ in range(100)}
    assert len(ipv6_addresses) == 100


@pytest.mark.parametrize("input_text, expected_map, case", [
    (
        "My IPs are 192.168.1.1 and 10.0.0.2.",
        {"192.168.1.1": None, "10.0.0.2": None},
        None
    ),
    (
        "IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        {"2001:0db8:85a3:0000:0000:8a2e:0370:7334": None},
        None
    ),
    (
        "IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        {"2001:0DB8:85A3:0000:0000:8A2E:0370:7334": None},
        "upper"
    ),
])
def test_redact_ip_addresses_from_text(input_text, expected_map, case):
    redacted_text, ip_address_map = redact_utils.redact_ip_addresses_from_text(
        input_text, case=case)
    # Check if all expected IP addresses are in the map and have been replaced
    for og_ip_address in expected_map.keys():
        assert og_ip_address in ip_address_map, f"{og_ip_address} not in {ip_address_map}"
        redacted_ip_address = ip_address_map[og_ip_address]
        assert og_ip_address not in redacted_text
        assert redacted_ip_address not in input_text, f"{redacted_ip_address} found in original text"
        assert redacted_ip_address in redacted_text, f"{redacted_ip_address} not found in redacted text"
