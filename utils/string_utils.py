import base64
import math
import random
import re
import string
import uuid
from typing import List, Set, Union

from utils.collections_utils import reverse_list


def is_string(var) -> bool:
    return isinstance(var, str)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def list_to_lower(data: Union[Set[str], List[str]]) -> List[str]:
    return [line.lower() for line in data]


def has_numbers(line: str) -> bool:
    return any(char.isdigit() for char in line)


def get_random_string(length: int) -> str:
    return ''.join(random.choice(string.ascii_letters) for i in range(length))


def get_random_number(length: int) -> str:
    return ''.join(random.choice(string.digits) for i in range(length))


def get_email_username(email: str) -> str:
    return email.split("@")[0]


def extract_ips(text: str) -> Set[str]:
    return set(re.findall(r'[0-9]+(?:\.[0-9]+){3}', text))


def generate_username(min_length: int, max_length: int):
    consonants = ('b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n',
                  'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')

    cons_weighted = (("t", "n"), ("r", "s", "h", "d"), ("l", "f", "c", "m"), ("g", "y", "p", "w", "b"),
                     ("v", "b", "j", "x", "q"), "z")
    vow_weighted = (("e", "a", "o"), ("i", "u"))
    double_cons = ("he", "re", "ti", "ti", "hi", "to", "ll", "tt", "nn", "pp", "th", "nd", "st", "qu")
    double_vow = ("ee", "oo", "ei", "ou", "ai", "ea", "an", "er", "in",
                  "on", "at", "es", "en", "of", "ed", "or", "as", '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')

    def get_consonant(is_double):
        if is_double:
            return random.choice(double_cons)  # add two consonants from our pre-defined tuple
        else:
            # we're just guessing at some good weights here. This is how more common letters get used more
            i = random.randrange(100)
            if i < 40:
                weight = 0
            elif 65 > i >= 40:
                weight = 1
            elif 80 > i >= 65:
                weight = 2
            elif 90 > i >= 80:
                weight = 3
            elif 97 > i >= 90:
                weight = 4
            else:
                # the last group is Z by it No point in going through extra code when we can finish it here
                return cons_weighted[5]
            # return a random consonant based on the weight
            return cons_weighted[weight][random.randrange(len(cons_weighted[weight]))]

    def get_vowel(is_double):
        if is_double:
            return random.choice(double_vow)  # add two vowels from our pre-defined tuple
        else:
            i = random.randrange(100)
            if i < 70:
                weight = 0
            else:
                weight = 1
            # return a random vowel based on the weight
            return vow_weighted[weight][random.randrange(len(vow_weighted[weight]))]

    username, is_double, num_length = "", False, 0  # reset variables
    if random.randrange(10) > 0:
        is_consonant = True
    else:
        is_consonant = False

    length = random.randrange(min_length, max_length)

    if random.randrange(5) == 0:  # decide if there will be numbers after the name
        num_length = random.randrange(3) + 1
        if length - num_length < 2:  # we don't want the username to be too short
            num_length = 0

    for j in range(length - num_length):  # we leave room for the numbers after the name here
        if len(username) > 0:
            if username[-1] in consonants:
                is_consonant = False
            elif username[-1] in consonants:
                is_consonant = True
        if not is_double:  # if the last character was a double, skip a letter
            # 1 in 8 chance of doubling if username is still short enough
            if random.randrange(8) == 0 and len(username) < int(length - num_length) - 1:
                is_double = True  # this character will be doubled
            if is_consonant:
                username += get_consonant(is_double)  # add consonant to username
            else:
                username += get_vowel(is_double)  # add vowel to username
            is_consonant = not is_consonant  # swap consonant/vowel value for next time
        else:
            is_double = False  # reset double status so the next letter won't be skipped
    if random.randrange(2) == 0:
        # this was the best method I could find to only capitalize the first letter in Python 3
        username = username[:1].upper() + username[1:]
    if num_length > 0:
        for j in range(num_length):  # loop 1 - 3 times
            username += str(random.randrange(10))  # append a random number, 0 - 9
    return username


def split_str(data: str, n: int) -> List[str]:
    return [data[i:i + n] for i in range(0, len(data), n)]


def reverse_str(data: str) -> str:
    return data[::-1]


def get_human_readable_size(size_in_bytes: int) -> str:
    str_size = str(int(size_in_bytes))
    return '_'.join(reverse_list([reverse_str(temp) for temp in split_str(reverse_str(str_size), 3)]))


def shannon_entropy(data: str):
    """
    Adapted from http://blog.dkbza.org/2007/05/scanning-data-for-entropy-anomalies.html
    by way of truffleHog (https://github.com/dxa4481/truffleHog)
    """
    if not data:
        return 0
    entropy: float = 0
    for x in string.printable:
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy


def decode_utf8(val: bytes, *, ignore_errors=True) -> str:
    if ignore_errors:
        return val.decode("utf-8", "ignore")
    return val.decode("utf-8")


def remove_non_ascii(text: str) -> str:
    return re.sub(r'[^\x00-\x7F]', '', text)


def base64_decode(val: str, *, ignore_errors=False) -> str:
    val += "=" * ((4 - len(val) % 4) % 4)
    return decode_utf8(base64.b64decode(val), ignore_errors=ignore_errors)


def base64_encode(val: str) -> str:
    sample_string_bytes = val.encode("ascii", "ignore")
    base64_bytes = base64.b64encode(sample_string_bytes)
    return base64_bytes.decode("ascii")


def is_base64_string(s: str) -> bool:
    try:
        return base64_encode(base64_decode(s)) == s
    except Exception:
        return False


def extract_emails(data: str) -> Set[str]:
    return set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', data))


def replace_last(data: str, old: str, new: str) -> str:
    return new.join(data.rsplit(old, 1))


def remove_nul_chars(data: str) -> str:
    return data.encode('ascii', 'ignore').decode("utf-8", errors="replace").replace("\x00", "")


def is_valid_android_package_name(name: str) -> bool:
    # The pattern ensures each segment starts with a letter, and contains only letters, numbers, or underscores.
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$'
    return bool(re.match(pattern, name))


def restrict_string_length(s: str, n: int) -> str:
    return s[:n]


def remove_substring(s: str, start_idx: int, end_idx: int) -> str:
    return s[:start_idx] + s[end_idx + 1:]


def remove_new_lines(s: str) -> str:
    return s.replace('\n', '')
