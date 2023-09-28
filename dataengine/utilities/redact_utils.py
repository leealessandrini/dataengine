import re
import random


MAC_REGEX = re.compile(
    # Mac with colons
    r"((?:[0-9A-Fa-f]{2}:{1}){5}[0-9A-Fa-f]{2})|"
    # Mac with dashes
    r"((?:[0-9A-Fa-f]{2}-{1}){5}[0-9A-Fa-f]{2})|"
    # Mac with no colons or dashes
    # Note: This will flag every 12 digit string as a mac because it is
    # technically valid
    r"([0-9A-Fa-f]{12})"
)
LOCAL_MAC_REGEX = re.compile(
    # First octet's second least significant bit must be 1
    r"((?:[0-9a-f][2637AaEeBbFf][:-]?){1}"
    r"([0-9A-Fa-f]{2}[:-]?){4}[0-9A-Fa-f]{2})")
IPv4_REGEX = re.compile(
    r"(?<![.\w])"  # Negative lookbehind
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    r"\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    r"\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    r"\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    r"(?!\w)"  # Negative lookahead for only word characters
)
# Partial source: https://stackoverflow.com/questions/53497
IPv6_REGEX = re.compile(
    r"(?<![.\w])"  # Negative lookbehind
    r"("  
    r"(([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|"
    r"(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|"
    r"((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|"
    r"(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|"
    r":((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|"
    r"(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|"
    r"((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|"
    r"(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|"
    r"((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|"
    r"(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|"
    r"((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|"
    r"(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|"
    r"((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|"
    r"(:(((:[0-9A-Fa-f]{1,4}){1,7})|"
    r"((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))"
    r")"
    r"(?!\w)"  # Negative lookahead for only word characters
)


def add_colons_to_mac(mac):
    """Add colons to a MAC address string.

    Args:
        mac (str):
            A 12-character MAC address string without any separators.

    Returns:
        str:
            The MAC address string with colons added between every two
            characters.

    Raises:
        ValueError: If the length of the input MAC address is not 12.

    Examples:
        >>> add_colons_to_mac("0123456789AB")
        "01:23:45:67:89:AB"

        >>> add_colons_to_mac("A1B2C3D4E5F6")
        "A1:B2:C3:D4:E5:F6"
    """
    if len(mac) != 12:
        raise ValueError("Invalid MAC address length")
    
    return ':'.join(mac[i:i+2] for i in range(0, 12, 2))


def find_unique_macs(text, case=None):
    """
    Find the unique mac addresses within some text.

    Args:
        text (str): text string
        case (str): specify whether to cast macs to uppercase or lowercase

    Returns:
        list of unique mac addresses
    """
    # Search for all MAC addresses in the text
    mac_addresses = re.findall(MAC_REGEX, text)
    # Since re.findall() returns tuples, convert them back to the original
    # mac addresses
    mac_addresses = ["".join(mac) for mac in mac_addresses]
    # Add colons to mac addresses if applicable
    mac_addresses = [
        add_colons_to_mac(mac) if ((":" not in mac) and ("-" not in mac))
        else mac.replace("-", ":") if ("-" in mac)
        else mac
        for mac in mac_addresses]
    # Cast to provided case if applicable
    if case == "upper":
        mac_addresses = [mac.upper() for mac in mac_addresses]
    elif case == "lower":
        mac_addresses = [mac.lower() for mac in mac_addresses]
    # Cast to a set in order to recude the list to unique macs
    unique_macs = list(set(mac_addresses))
    # Sort the list before returning it
    unique_macs.sort()

    return unique_macs


def generate_random_mac():
    """
    Generate a random mac address.

    Returns:
        random mac address
    """
    return ":".join("{:02x}".format(random.randint(0, 255)) for _ in range(6))


def generate_random_local_mac():
    """
    Generate a random local MAC address.

    The function generates a random MAC address and ensures that it is a local
    MAC address by setting the second least significant bit of the first octet
    to 1.

    Returns:
        str:
            A MAC address string in the format "XX:XX:XX:XX:XX:XX", where each
            "XX" is a two-digit hexadecimal number.

    Examples:
        >>> generate_random_local_mac()
        "01:23:45:67:89:AB"

        >>> generate_random_local_mac()
        "1A:2B:3C:4D:5E:6F"
    """
    # Generate a random 8-bit number (0-255)
    first_octet = random.randint(0, 255)
    # Set the second least significant bit to 1
    first_octet |= 2
    # Generate the remaining octets
    mac_address = [first_octet] + [random.randint(0, 255) for _ in range(5)]
    # Convert to hexadecimal and join with colons
    return ':'.join(f'{octet:02x}' for octet in mac_address)


def redact_macs_from_text(text, mac_map=None, case=None):
    """
    Provided some text, redact the original macs.

    Args:
        text (str): text string
        mac_map (dict): key value pairs of og macs and random macs
        case (str): specify whether to cast macs to uppercase or lowercase

    Returns:
        redacted text and updated mac map
    """
    # Pull unique mac lists
    mac_list = find_unique_macs(text, case=case)
    # If existing map is passed update it
    if mac_map:
        for og_mac in mac_list:
            if og_mac not in mac_map:
                # If the mac is a local mac just map it to itself
                if LOCAL_MAC_REGEX.fullmatch(og_mac):
                    mac_map.update({og_mac: og_mac})
                # Otherwise map the op mac to a randomly generated local mac
                else:
                    mac_map.update({og_mac: generate_random_local_mac()})
    # Otherwise create map of original mac address to random mac address
    else:
        mac_map = {
            og_mac: og_mac if LOCAL_MAC_REGEX.fullmatch(og_mac)
            else generate_random_local_mac()
            for og_mac in mac_list}
    # Replace instances of macs in text
    redacted_text = text
    # Replace each original mac with a redacted mac
    for og_mac, redacted_mac in mac_map.items():
        # Conduct replacement for all possible permutations
        for permuation in [None, "-", ""]:
            if permuation:
                mac_permutation = og_mac.replace(":", permuation)
            else:
                mac_permutation = og_mac
        # Replace uppercase
        redacted_text = redacted_text.replace(
            mac_permutation.upper(), redacted_mac)
        # Replace lowercase
        redacted_text = redacted_text.replace(
            mac_permutation.lower(), redacted_mac)

    return redacted_text, mac_map


def find_unique_ipv4(text):
    """
    Finds and returns the unique IPv4 addresses in a given text.
    
    Args:
        text (str): The text to search for IPv4 addresses.
        
    Returns:
        list: A sorted list of unique IPv4 addresses found in the text.
    """
    ipv4_addresses = re.findall(IPv4_REGEX, text)
    unique_ipv4_addresses = list(set(ipv4_addresses))
    unique_ipv4_addresses.sort()

    return unique_ipv4_addresses


def find_unique_ipv6(text, case=None):
    """
    Finds and returns the unique IPv6 addresses in a given text.
    
    Args:
        text (str): The text to search for IPv6 addresses.
        
    Returns:
        list: A sorted list of unique IPv6 addresses found in the text.
    """
    ipv6_addresses = [
        match[0] for match in re.findall(IPv6_REGEX, text)]
    if case == "upper":
        ipv6_addresses = [ipv6.upper() for ipv6 in ipv6_addresses]
    elif case == "lower":
        ipv6_addresses = [ipv6.lower() for ipv6 in ipv6_addresses]
    unique_ipv6_addresses = list(set(ipv6_addresses))
    unique_ipv6_addresses.sort()

    return unique_ipv6_addresses


def generate_random_ipv4():
    """
    Generates a random IPv4 address.
    
    Returns:
        str: A random IPv4 address.
    """
    return ".".join(str(random.randint(0, 255)) for _ in range(4))


def generate_random_ipv6():
    """
    Generates a random IPv6 address.
    
    Returns:
        str: A random IPv6 address.
    """
    return ":".join("{:x}".format(random.randint(0, 0xFFFF)) for _ in range(8))


def redact_ip_addresses_from_text(text, ip_address_map=None, case=None):
    """
    Provided some text, redact the original ip addresses.

    Args:
        text (str): text string
        ip_address_map (dict): key value pairs of og addresses and random ones
        case (str): specify whether to cast addresses to uppercase or lowercase

    Returns:
        redacted text and updated ip address map
    """
    # Pull unique mac lists
    ipv4_addresses = find_unique_ipv4(text)
    ipv6_addresses = find_unique_ipv6(text, case=case)
    # If existing map is passed update it
    if ip_address_map:
        # Update IPv4 Addresses
        ip_address_map.update({
            og_ip_address: generate_random_ipv4()
            for og_ip_address in ipv4_addresses
            if og_ip_address not in ip_address_map})
        # Update IPv6 Addresses
        ip_address_map.update({
            og_ip_address: generate_random_ipv6()
            for og_ip_address in ipv6_addresses
            if og_ip_address not in ip_address_map})
    # Otherwise create map of original mac address to random mac address
    else:
        ip_address_map = {
            og_ip_address: generate_random_ipv4()
            for og_ip_address in ipv4_addresses}
        ip_address_map.update({
            og_ip_address: generate_random_ipv6()
            for og_ip_address in ipv6_addresses})
    # Replace instances of macs in text
    redacted_text = text
    # Replace each original mac with a redacted mac
    for og_ip_address, redacted_ip_address in ip_address_map.items():
        # TODO: Handle mixed case in text
        # Replace uppercase
        redacted_text = redacted_text.replace(
            og_ip_address.upper(), redacted_ip_address)
        # Replace lowercase
        redacted_text = redacted_text.replace(
            og_ip_address.lower(), redacted_ip_address)

    return redacted_text, ip_address_map
