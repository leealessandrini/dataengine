import re
import random
import itertools
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pool


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


def generate_combinations(s, start=0, current="", result=[]):
    if start == len(s):
        result.append(current)
        return
    generate_combinations(s, start + 1, current + s[start].lower(), result)
    generate_combinations(s, start + 1, current + s[start].upper(), result)

    return list(set(result))


def convert_to_hex(decimal):
    """
    Convert to hexadecimal with leading zeros.
    """
    return "{:02x}".format(decimal)


def left_pad_zeros(word: str) -> str:
    """
    Left-pad zeros to a string based on the initial zeros in the input word.

    This function takes a word, counts the number of leading zeros, and
    returns a string that represents the left-padding format to be used for
    similar words.

    Args:
        word (str):
            The input word containing initial zeros and other characters.

    Returns:
        str:
            A string representing the left-padding format, e.g., "0{0,2}".
        
    Examples:
        >>> left_pad_zeros("0045")
        '0{0,2}45'
        
        >>> left_pad_zeros("45")
        '45'
        
        >>> left_pad_zeros("000")
        '0{1,3}'
    """
    if word == "0":
        return word
    elif re.compile("0+").fullmatch(word):
        return f"0{{1,{len(word)}}}"
    zeros = 0
    for i in word:
        if i == "0":
            zeros += 1
        else:
            break
    # Return regex for the word
    if zeros:
        return f"0{{0,{zeros}}}" + word[zeros:]
    else:
        return word


def generate_alphanumeric_regex(alphanumeric_string: str) -> str:
    """
    Generate a regular expression for a given alphanumeric string.

    The function takes an alphanumeric string consisting of alphabetic
    characters and digits, and generates a corresponding regular expression.
    For each alphabetic character, a range consisting of the uppercase and
    lowercase versions is created. Digits are included as-is in the regex.

    Args:
        alphanumeric_string (str):
            The input alphanumeric string consisting of alphabetic characters
            and digits.

    Returns:
        str:
            A regular expression string that can be used to match the given
            alphanumeric string.

    Example:
        >>> generate_alphanumeric_regex("Ab1")
        '[Aa]{1}[Bb]{1}1'
    """
    return "".join(
        f"[{char.upper()}{char.lower()}]{{1}}" if char.isalpha() else char
        for char in alphanumeric_string)


def generate_mac_regex(mac_address: str) -> re.Pattern:
    """
    Generate a regular expression for matching a given MAC address.

    This function takes a MAC address as input, normalizes it by removing
    any colons or dashes, and then generates a regular expression that can
    match the MAC address in various formats (plain, colon-separated, and
    dash-separated).

    Args:
        mac_address (str):
            The input MAC address as a string. It can contain colons or dashes
            as separators.

    Returns:
        re.Pattern:
            A compiled regular expression pattern that can be used to match
            the given MAC address in its various formats.

    Example:
        >>> pattern = generate_mac_regex("AA:BB:CC:DD:EE:FF")
        >>> bool(pattern.match("aabbccddeeff"))
        True
        >>> bool(pattern.match("AA:BB:CC:DD:EE:FF"))
        True
        >>> bool(pattern.match("AA-BB-CC-DD-EE-FF"))
        True
    """
    # Normalize the mac address
    normal_mac = mac_address.replace(":", "").replace("-", "")
    # Split the normalized mac into it's respective octets and cast each to a
    # regex that handles case sensitivity
    octets = [
        generate_alphanumeric_regex(normal_mac[i:i + 2])
        for i in range(0, 12, 2)]
    # Generate final mac regex that handles all possible valid permutations
    return re.compile("|".join([i.join(octets) for i in ["", ":", "-"]]))


def generate_ipv4_regex(ipv4_address: str) -> re.Pattern:
    """
    Generate a regex pattern to match the given IPv4 address and its
    equivalent IPv6 representations.

    This function takes an IPv4 address, converts it to its IPv6 hexadecimal
    block form, and constructs a regex pattern to match all valid permutations
    of the address.

    Args:
        ipv4_address (str):
            The IPv4 address to be converted, e.g., "192.168.1.1".

    Returns:
        re.Pattern:
            A regex pattern that matches the IPv4 address and its IPv6
            equivalents.
    """
    base_str = "(::[Ff]{4}:|0{1,4}:0{1,4}:0{1,4}:0{1,4}:0{1,4}:[Ff]{4}:){1}"
    # Pull octets from ip address and cast them to hexadecimal
    octets = [
        convert_to_hex(int(decimal)) for decimal in ipv4_address.split(".")]
    # Get last two 16-bit words in final 32 bits of IPv6 Address
    word_1 = left_pad_zeros(generate_alphanumeric_regex("".join(octets[0:2])))
    word_2 = left_pad_zeros(generate_alphanumeric_regex("".join(octets[2:])))
    # Return IPv4 regex that supports all valid permutations
    return re.compile(
        ipv4_address.replace(".", "\\.") + "|" + base_str + "((" +
        ipv4_address.replace(".", "\\.") + ")|(" + ":".join([word_1, word_2]) +
        ")){1}")


def generate_ipv6_regex(ipv6_address: str) -> re.Pattern:
    """
    Generates a regex pattern to match the given a decompressed IPv6 address.
    
    Args:
        ipv6_address (str): The IPv6 address to generate a regex for.
        
    Returns:
        re.Pattern:
            A compiled regex pattern that can match the IPv6
            address and its compressed forms.
                      
    Examples:
        >>> generate_ipv6_regex("2001:0db8::ff00:0042:8329")
        <regex object>
    """
    # Split the ip address into 16 bit blocks
    blocks = ipv6_address.split(":")
    # Get the initial permutation
    permutations = [
        ":".join([
            left_pad_zeros(
                generate_alphanumeric_regex(block)
            ) for block in blocks])]
    # Generate zero ranges for ip address
    zero_ranges = []
    in_range = False
    for index, word in enumerate(blocks):
        if (
            (not in_range) and
            (re.compile(r"0{1,4}").fullmatch(word))
        ):
            zero_ranges.append([index])
            in_range = True
        elif (
            (in_range) and
            (not re.compile(r"0{1,4}").fullmatch(word))
        ):
            zero_ranges[-1].append(index)
            in_range = False
    # If the last word is 0 set the final zero range value
    if in_range:
        zero_ranges[-1].append(index)
    # Generate compressed permutations
    # If all the digits are 0 then the compressed format is ::
    if all(char == "0" for char in ipv6_address if char != ":"):
        permutations.append("::")
    else:
        permutations += [
            ":".join([
                i for i in [
                    left_pad_zeros(
                        generate_alphanumeric_regex(word)
                    ) if not (
                        index >= zero_range[0] and
                        index < zero_range[1]
                    ) else ""
                    if index == (zero_range[1] - 1) else None
                    for index, word in enumerate(blocks)
                ] if i is not None])
            for zero_range in zero_ranges]

    return re.compile("|".join(permutations))


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


def find_unique_macs(text):
    """
    Find the unique mac addresses within some text.

    Args:
        text (str): text string

    Returns:
        list of unique mac addresses
    """
    # Search for all MAC addresses in the text
    mac_addresses = re.findall(MAC_REGEX, text)
    # Since re.findall() returns tuples, convert them back to the original
    # mac addresses and make sure they're uppercase
    mac_addresses = [
        "".join(mac).upper() for mac in mac_addresses
        # TODO: See if this can be moved to original regex
        # Filter all 12 digit matches
        if not re.compile(r"[0-9]{12}").fullmatch("".join(mac))]
    # Add colons to mac addresses if applicable
    mac_addresses = [
        add_colons_to_mac(mac) if ((":" not in mac) and ("-" not in mac))
        else mac.replace("-", ":") if ("-" in mac)
        else mac
        for mac in mac_addresses]
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


def redact_macs_from_text(text, mac_map=None):
    """
    Provided some text, redact the original macs.

    Args:
        text (str): text string
        mac_map (dict): key value pairs of og macs and random macs

    Returns:
        redacted text and updated mac map
    """
    base_str = "[REDACTED:MAC:{}]"
    # Pull unique mac lists
    mac_list = find_unique_macs(text)
    # If existing map is passed update it
    if not mac_map:
        mac_map = {
            f"[REDACTED:MAC:{index + 1}]": {
                "original": mac,
                "regex": generate_mac_regex(mac)}
            for index, mac in enumerate(mac_list)}
    else:
        mac_count = sum(True for key in mac_map.keys() if "MAC" in key)
        for og_mac in mac_list:
            #if og_mac not in mac_map:
            if not any(
                bool(value["regex"].fullmatch(og_mac))
                for value in mac_map.values()
            ):
                mac_count += 1
                mac_map[base_str.format(mac_count)] = {
                    "original": og_mac, "regex": generate_mac_regex(og_mac)}
    # Replace instances of macs in text
    redacted_text = text
    # Replace each original mac with a redacted mac
    for redaction_string, values in mac_map.items():
        redacted_text = re.sub(
            values["regex"], redaction_string, redacted_text)

    return redacted_text, mac_map


def decompress_ipv6(ipv6_address: str) -> str:
    """
    Decompress a compressed IPv6 address to its full 8-block hexadecimal form.
    
    Given a compressed IPv6 address, this function will expand it into its
    full 8-block representation. Each block in the full form consists of 4
    hexadecimal digits. The function handles the following scenarios:
    
    1. Expands the '::' shorthand to the appropriate number of zero blocks.
    2. Pads existing blocks with leading zeros to ensure 4 digits.
    
    Args:
        ipv6_address (str):
            The compressed IPv6 address to decompress. It can also be an IPv6
            address that's partially compressed or already in full form.
        
    Returns:
        str: The IPv6 address in its full 8-block, 4-digits-per-block form.
    
    Example:
        >>> decompress_ipv6("1080::8:800:417A")
        "1080:0000:0000:0000:0008:0800:417A"
        
        >>> decompress_ipv6("::1")
        "0000:0000:0000:0000:0000:0000:0000:0001"
        
        >>> decompress_ipv6("2001:db8::ff00:42:8329")
        "2001:0db8:0000:0000:0000:ff00:0042:8329"
        
    Notes:
        - The function assumes that the input is a valid IPv6 address.
        - The function does not validate the IPv6 address.
    """
    # Split the IPv6 address by the double colon "::"
    halves = ipv6_address.split("::")
    # If there's no double colon, the address is already in full form
    if len(halves) == 1:
        # Still need to pad with leading zeros for each block
        blocks = ipv6_address.split(":")
        full_blocks = [block.zfill(4) for block in blocks]
        return ":".join(full_blocks)
    # Split each half into its 16-bit blocks
    first_half = halves[0].split(":") if halves[0] else []
    second_half = halves[1].split(":") if halves[1] else []
    # Pad with leading zeros for each block in the halves
    first_half = [block.zfill(4) for block in first_half]
    second_half = [block.zfill(4) for block in second_half]
    # Calculate the number of zero blocks needed for padding
    num_zero_blocks = 8 - (len(first_half) + len(second_half))
    # Create the zero blocks
    zero_blocks = ["0000"] * num_zero_blocks
    # Combine all the blocks to form the full IPv6 address
    full_address_blocks = first_half + zero_blocks + second_half
    # Join the blocks into a full IPv6 address
    full_address = ":".join(full_address_blocks)
    
    return full_address



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


def find_unique_ipv6(text):
    """
    Finds and returns the unique IPv6 addresses in a given text.
    
    Args:
        text (str): The text to search for IPv6 addresses.
        
    Returns:
        list: A sorted list of unique IPv6 addresses found in the text.
    """
    # Find and cast each mac address to uppercase
    ipv6_addresses = [
        decompress_ipv6(match[0].upper())
        for match in re.findall(IPv6_REGEX, text)]
    # Decompress mac addresses
    # TODO: Remove the if statement once this bug is figured out for 18 octet
    #       macs. Make sure ipv6 regex doesn't pick these up
    ipv6_addresses = [
        i for i in ipv6_addresses
        if not all(len(j) == 2 for j in i.split(":"))]
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


def redact_ip_addresses_from_text(text, ip_address_map=None):
    """
    Provided some text, redact the original ip addresses.

    Args:
        text (str): text string
        ip_address_map (dict): key value pairs of og addresses and random ones

    Returns:
        redacted text and updated ip address map
    """
    # Replace instances of macs in text
    redacted_text = text
    # Setup base redaction strings
    ipv4_base_str = "[REDACTED:IPv4:{}]"
    ipv6_base_str = "[REDACTED:IPv6:{}]"
    # Pull unique mac lists
    ipv4_addresses = find_unique_ipv4(text)
    ipv6_addresses = find_unique_ipv6(text)
    # Build initial map if None was passed
    if not ip_address_map:
        ip_address_map = {
            ipv4_base_str.format(index + 1): {
                "original": og_ip_address,
                "regex": generate_ipv4_regex(og_ip_address)
            } for index, og_ip_address in enumerate(ipv4_addresses)}
        ip_address_map.update({
            ipv6_base_str.format(index + 1): {
                "original": og_ip_address,
                "regex": generate_ipv6_regex(og_ip_address)
            } for index, og_ip_address in enumerate(ipv6_addresses)})
    else:
        # Update IPv4 Addresses
        ipv4_count = sum(True for key in ip_address_map.keys() if "v4" in key)
        for og_ip_address in ipv4_addresses:
            if not any(
                bool(value["regex"].fullmatch(og_ip_address))
                for value in ip_address_map.values()
            ):
                ipv4_count += 1
                ip_address_map[ipv4_base_str.format(ipv4_count)] = {
                    "original": og_ip_address,
                    "regex": generate_ipv4_regex(og_ip_address)}
        # Update IPv6 Addresses
        ipv6_count = sum(True for key in ip_address_map.keys() if "v6" in key)
        for og_ip_address in ipv6_addresses:
            if not any(
                bool(value["regex"].fullmatch(og_ip_address))
                for value in ip_address_map.values()
            ):
                ipv6_count += 1
                ip_address_map[ipv6_base_str.format(ipv6_count)] = {
                    "original": og_ip_address,
                    "regex": generate_ipv6_regex(og_ip_address)}
    # Replace each original mac with a redacted mac
    for redaction_string, values in ip_address_map.items():
        redacted_text = re.sub(
            values["regex"], redaction_string, redacted_text)

    return redacted_text, ip_address_map


def redact_items_from_text(text, redact_map):
    """
    Redact sensitive information from a given text based on a redaction map.
    
    Args:
        text (str): The original text where redaction needs to be performed.
        redact_map (dict):
            A mapping containing the redaction keys and associated regular
            expressions.

    Returns:
        str: The redacted text.    
    """
    # Make a copy of the original text
    redacted_text = text
    # Redact all full matches from the redaction map
    for redaction_string, values in redact_map.items():
        redacted_text = values["regex"].sub(redaction_string, redacted_text)
    
    return redacted_text


def pooled_find(find_function, text_list, max_workers=16):
    """
    Execute a find function in parallel on a list of texts.
    
    Args:
        find_function (callable):
            The function to execute on each text in the list.
        text_list (list of str): The list of texts to process.
        max_workers (int, optional):
            The maximum number of worker processes. Defaults to 16.
    
    Returns:
        list:
            A list containing the results of applying find_function to each
            text in text_list.
    """
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(find_function, text_list))

    return results


def pooled_redact_text(redact_map, text_list, max_workers=16):
    """
    Perform redaction in parallel on a list of texts using a redaction map.
    
    Args:
        redact_map (dict):
            A mapping containing the redaction keys and associated regular
            expressions.
        text_list (list of str): The list of texts to redact.
        max_workers (int, optional):
            The maximum number of worker processes. Defaults to 16.
    
    Returns:
        list: A list containing the redacted texts.
    """
    with Pool(processes=max_workers) as executor:
        results = list(executor.starmap(
            redact_items_from_text,
            [(text, redact_map) for text in text_list]))

    return results


def redact_text(text_list):
    """
    Perform redaction of MAC addresses and IP addresses on a list of text strings.
    
    Args:
        text_list (list of str):
            The list of texts where redaction needs to be performed.
    
    Returns:
        list: A list of redacted text strings.
    """
    # Get unique mac list
    unique_macs_list = list(set(itertools.chain.from_iterable(
        pooled_find(find_unique_macs, text_list))))
    # Create initial redaction map with macs
    redact_map = {
        f"[REDACTED:MAC:{index + 1}]": {
            "original": mac,
            "regex": generate_mac_regex(mac)}
        for index, mac in enumerate(unique_macs_list)}
    # Get unique ip addresses and add them to redact map
    ipv4_base_str = "[REDACTED:IPv4:{}]"
    ipv6_base_str = "[REDACTED:IPv6:{}]"
    unique_ipv4_list = list(set(itertools.chain.from_iterable(
        pooled_find(find_unique_ipv4, text_list))))
    unique_ipv6_list = list(set(itertools.chain.from_iterable(
        pooled_find(find_unique_ipv6, text_list))))
    redact_map.update({
        ipv4_base_str.format(index + 1): {
            "original": og_ip_address,
            "regex": generate_ipv4_regex(og_ip_address)
        } for index, og_ip_address in enumerate(unique_ipv4_list)})
    redact_map.update({
        ipv6_base_str.format(index + 1): {
            "original": og_ip_address,
            "regex": generate_ipv6_regex(og_ip_address)
        } for index, og_ip_address in enumerate(unique_ipv6_list)})
    # Return list of redacted text strings
    return pooled_redact_text(redact_map, text_list)
