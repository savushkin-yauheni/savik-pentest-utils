import asyncio
import dataclasses
import http
import json
import re
import time
from dataclasses import dataclass
from http import HTTPStatus  # type: ignore
from http.cookies import SimpleCookie
from shlex import quote
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from loguru import logger
from multidict import CIMultiDict

from utils.collections_utils import merge_dicts


@dataclass(frozen=True)
class RequestConfig:
    url: str
    headers: Dict = dataclasses.field(default_factory=dict)
    cookies: Dict = dataclasses.field(default_factory=dict)
    body: Dict = dataclasses.field(default_factory=dict)
    method: str = 'GET'
    json: bool = False
    redirect: bool = True
    timeout: int = 7
    id: str = ''

    @classmethod
    def from_json(cls, data):
        return cls(url=data['url'], headers=data['headers'], cookies=data['cookies'], body=data['body'],
                   method=data['method'], json=data['json'], redirect=data['redirect'],
                   timeout=data['timeout'], id=data['id'], )


@dataclass(frozen=True)
class ClientResponse:
    url: str
    method: str
    text: str
    headers: Dict[str, List[str]]
    response_time: float
    status: int
    history: List = dataclasses.field(default_factory=list)

    def headers_contain_text(self, text: str, *, ignore_case: bool = True) -> bool:
        for header_name, header_values in self.headers.items():
            for header_value in header_values:
                if ignore_case:
                    new_text = text.lower()
                    if new_text in header_name.lower() or new_text in header_value.lower():
                        return True
                else:
                    if text in header_name or text in header_value:
                        return True
        return False

    def body_contains_text(self, text: str, *, ignore_case: bool = False) -> bool:
        return text.lower() in self.text.lower() if ignore_case else text in self.text

    def body_contains_any_text(self, texts: List[str], *, ignore_case: bool = False) -> bool:
        return any([text.lower() in self.text.lower() if ignore_case else text in self.text for text in texts])

    def get_text_occurrences_and_n_before(self, text: str, n: int) -> List[str]:
        indexes = [m.start() for m in re.finditer(text.lower(), self.text.lower())]
        return [
            self.text[index - n:index + len(text)] if index - n >= 0 else self.text[:index + len(text)]
            for index in indexes
        ]

    def get_cookies_dict(self) -> Dict[str, str]:
        set_cookie_values = CIMultiDict(self.headers).get('set-cookie') or []
        result = {}
        for set_cookie_value in set_cookie_values:
            try:
                cookie: SimpleCookie = SimpleCookie()
                cookie.load(set_cookie_value)
                result.update({key: value.value for key, value in cookie.items()})
            except http.cookies.CookieError:
                logger.debug(f'[get_cookies_dict] cookie parsing exception: {set_cookie_value}')
        return result

    def json(self):
        return parse_to_json(self.text)

    def __repr__(self):
        headers_str = '\n'.join([f'{k}: {v}' for k, v in self.headers.items()])
        return f'HTTP/2 {self.status}\n{headers_str}\n\n{self.text}'


def parse_to_json(data: str) -> Dict:
    return json.loads(data)


def post_request(url: str, *, data=None, cookies=None, proxies=None, headers=None, timeout: Optional[int] = 15,
                 allow_redirects: bool = True, json: Dict = None, session=None, ):
    func = (session or requests).post  # type: ignore
    return func(  # type: ignore
        url, data, verify=False, headers=headers, json=json,
        allow_redirects=allow_redirects, cookies=cookies, proxies=proxies, timeout=timeout
    )


def send_requests(
        configs: List[RequestConfig], *, proxy: Optional[str] = None,
        max_concurrent_connections: int = 200, headers: Dict[str, str] = None,
) -> List[Tuple[RequestConfig, ClientResponse]]:
    if not configs:
        return []
    responses = asyncio.run(_make_requests_async_version(
        configs=configs, proxy=proxy, max_concurrent_connections=max_concurrent_connections, headers=headers))
    return [response for response in responses if response[1]]  # type: ignore


async def _make_requests_async_version(
        configs: List[RequestConfig], *, max_concurrent_connections: int = 500, proxy: Optional[str] = None,
        headers: Dict[str, str] = None,
) -> List[
    Tuple[RequestConfig, Optional[ClientResponse]]]:
    tasks = []
    sem = asyncio.Semaphore(max_concurrent_connections)
    for config in configs:
        tasks.append(
            aiohttp_request(config=config, sem=sem, proxy=proxy, headers=headers, )
        )
    responses = await asyncio.gather(*tasks)
    return responses


async def aiohttp_request(
        config: RequestConfig, sem: asyncio.Semaphore, proxy: Optional[str] = None,
        headers: Dict[str, str] = None,
) -> Tuple[RequestConfig, Optional[ClientResponse]]:
    headers = headers or {}
    url = config.url
    headers = merge_dicts(
        headers, {
            'X-Bug-Bounty': 'HackerOne-savik',
            'X-HackerOne': 'savik',
            'ResearcherContact': 'savik@wearehackerone.com',
        },
        config.headers,
    )
    async with sem:
        try:
            async with ClientSession(timeout=ClientTimeout(total=config.timeout),
                                     connector=TCPConnector(ssl=False)) as session:
                start_time = time.monotonic()
                if config.method == 'GET':
                    method = session.get(url=url, headers=headers, cookies=config.cookies,
                                         allow_redirects=config.redirect, proxy=proxy)
                elif config.method == 'POST':
                    if config.json:
                        method = session.post(url=url, headers=headers, json=config.body, cookies=config.cookies,
                                              allow_redirects=config.redirect, proxy=proxy)
                    else:
                        method = session.post(url=url, headers=headers, data=config.body, cookies=config.cookies,
                                              allow_redirects=config.redirect, proxy=proxy)
                else:
                    raise Exception(f'method in unknown: {config.method}')
                async with method as resp:

                    return config, await convert_aio_client_response_to_my(resp, start_time)
        except Exception as ex:
            return config, None


async def convert_aio_client_response_to_my(
        resp: aiohttp.ClientResponse, start_time: float, *, disable_history: bool = False,
) -> ClientResponse:
    history_records = []
    if not disable_history:
        history_records = [
            await convert_aio_client_response_to_my(history, start_time, disable_history=True)
            for history in resp.history
        ]
    try:
        text_ = await resp.text()
    except Exception as ex:
        # logger.debug(f'[convert_aio_client_response_to_my] get response text exception: {resp.request_info.url} {ex}')
        text_ = ''
    response_time = time.monotonic() - start_time
    return map_aio_client_response_to_my(resp, text_, response_time, history_records)


def map_aio_client_response_to_my(resp: aiohttp.ClientResponse, text: str, response_time: float,
                                  history_records: List[ClientResponse]) -> ClientResponse:
    headers: Dict[str, List[str]] = {}
    for header_name, header_value in resp.headers.items():
        headers.setdefault(header_name, []).append(header_value)
    return ClientResponse(
        method=resp.method, url=str(resp.request_info.url), response_time=response_time,
        status=resp.status, headers=headers, text=text, history=history_records
    )


def to_cookie_string(cookies: Dict[str, str]):
    return "; ".join([str(x) + "=" + str(y) for x, y in cookies.items()])


def to_curl(request: RequestConfig, compressed=False, verify=False, proxy: str = '', ):
    parts = [
        ('curl', None),
        ('-X', request.method),
    ]

    if len(request.cookies):
        parts += [('-H', 'Cookie: {0}'.format(to_cookie_string(request.cookies)))]

    for k, v in sorted(request.headers.items()):
        parts += [('-H', '{0}: {1}'.format(k, v))]

    if proxy:
        parts += [('-x', proxy)]

    if request.body:
        if request.json:
            body = json.dumps(request.body)  # type: ignore
        else:
            body = '&'.join([f'{k}={v}' for k, v in request.body.items()])  # type: ignore
        parts += [('-d', body)]  # type: ignore

    if compressed:
        parts += [('--compressed', None)]

    if not verify:
        parts += [('--insecure', None)]

    parts += [(None, str(request.url))]  # type: ignore

    flat_parts = []
    for k, v in parts:  # type: ignore
        if k:
            flat_parts.append(quote(k))
        if v:
            flat_parts.append(quote(v))

    return ' '.join(flat_parts)
