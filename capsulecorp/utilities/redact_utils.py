import re
import random


MAC_REGEX = re.compile(r"((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})")
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
        mac_map.update({
            og_mac: generate_random_mac()
            for og_mac in mac_list if og_mac not in mac_map})
    # Otherwise create map of original mac address to random mac address
    else:
        mac_map = {og_mac: generate_random_mac() for og_mac in mac_list}
    # Replace instances of macs in text
    redacted_text = text
    # Replace each original mac with a redacted mac
    for og_mac, redacted_mac in mac_map.items():
        # Replace uppercase
        redacted_text = redacted_text.replace(og_mac.upper(), redacted_mac)
        # Replace lowercase
        redacted_text = redacted_text.replace(og_mac.lower(), redacted_mac)

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
