import re
import random


MAC_REGEX = re.compile(r"((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})")


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
    # list of unique mac addresses
    unique_macs = list({"".join(mac) for mac in mac_addresses})
    # Cast to provided case if applicable
    if case == "upper":
        unique_macs = [mac.upper() for mac in unique_macs]
    elif case == "lower":
        unique_macs = [mac.lower() for mac in unique_macs]
    
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
