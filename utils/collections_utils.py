import collections
import random
from collections.abc import Iterable
from typing import List, Set, Union, Dict, TypeVar, ValuesView, KeysView

T = TypeVar('T')


def split_list(lst: List, n: int) -> List[List]:
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def split_list_n_parts(lst: List, n: int):
    if not lst:
        return []
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]


def reverse_list(data: List) -> List:
    return data[::-1]


def merge_collections_to_set(*args) -> Set:
    result = set()
    for i in args:
        result.update(i)
    return result


def flat_list_of_lists(
        list_of_lists: Union[List[List], List[Set], Set[Set], ValuesView[Set], ValuesView[List]]) -> List:
    return [item for sublist in list_of_lists for item in sublist]


def lists_are_equal(first: List, second: List) -> bool:
    return collections.Counter(first) == collections.Counter(second)


def uniq_list(*args) -> List:
    return list(merge_collections_to_set(*args))


def merge_dicts(*args) -> Dict:
    result: Dict = {}
    for i in args:
        result = {**result, **i}
    return result


def is_iterable(obj):
    return isinstance(obj, Iterable)


def is_collection(obj):
    return is_iterable(obj) and not isinstance(obj, str)


def is_list(obj):
    return isinstance(obj, list)


def is_dict(obj):
    return isinstance(obj, dict)


def get_collections_intersection(first: Union[List, Set], second: Union[List, Set]) -> List:
    return list(set(first) & set(second))


def remove_empties(data: Union[List[T], Set[T]]) -> List[T]:
    return list(filter(None, data))


def remove_none(data: Union[List[T], Set[T]]) -> List[T]:
    temp = list(data)
    return [x for x in temp if x is not None]


def shuffle_collection(data: Union[List, Set, KeysView]) -> List:
    collection_copy = list(data)
    random.shuffle(collection_copy)
    return collection_copy


def flatten_nested_dict(d: Union[Dict, collections.abc.MutableMapping]) -> Dict:
    items: List = []
    for k, v in d.items():
        new_key = k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten_nested_dict(v).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_random_element(collection: Union[List, Set]):
    return random.choice(list(collection))


def restrict_collection_length(collection: Union[List, Set], max_length: int):
    if len(collection) > max_length:
        list_collection = shuffle_collection(collection)[0:max_length]
        if type(collection) == list:
            return list_collection
        return set(list_collection)
    return collection


def merge_scans(*scan_results: Dict[str, Set]) -> Dict[str, Set]:
    result: Dict = {}
    for scan_result in scan_results:
        for web_host, scans in scan_result.items():
            result.setdefault(web_host, set()).update(scans)
    return result


def convert_one_to_one_dict_to_one_to_many_dict_str(data: Dict[str, str]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for k, v in data.items():
        result.setdefault(v, []).append(k)
    return result


def convert_one_to_many_dict_to_one_to_many_dict_str(data: Dict[str, List[str]]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for k, v in data.items():
        for i in v:
            result.setdefault(i, []).append(k)
    return result


def get_first_dict_value(data: Dict):
    return next(iter(data.values()))
