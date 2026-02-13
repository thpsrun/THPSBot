import asyncio
import re
from dataclasses import dataclass
from typing import Any

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError, ClientConnectorError


@dataclass
class AIOHTTPResponse:
    status: int
    data: Any | None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class ServiceUnavailableError(Exception):
    def __init__(self, host: str, attempts: int):
        self.host = host
        self.attempts = attempts
        super().__init__(
            f"{host} appears to be offline after {attempts} failed attempts"
        )


class AIOHTTPHelper:
    _session: aiohttp.ClientSession | None = None
    _host_failures: dict[str, int] = {}
    _max_failures: int = 20
    _reconnecting: bool = False

    @staticmethod
    def _extract_host(
        url: str,
    ) -> str:
        match = re.match(r"https?://([^/]+)", url)
        return match.group(1) if match else url

    @classmethod
    async def init_session(
        cls,
    ) -> None:
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession()

    @classmethod
    async def close_session(
        cls,
    ) -> None:
        if cls._session and not cls._session.closed:
            await cls._session.close()

    @classmethod
    async def _request(
        cls,
        method: str,
        url: str,
        headers: dict[str, str] | None,
        data: dict[str, Any] | None = None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        if cls._session is None or cls._session.closed:
            await cls.init_session()

        assert cls._session is not None
        host = cls._extract_host(url)

        kwargs: dict[str, Any] = {
            "headers": headers,
            "timeout": aiohttp.ClientTimeout(total=timeout),
        }
        if data is not None:
            kwargs["json"] = data

        try:
            async with cls._session.request(method, url, **kwargs) as response:
                cls._host_failures[host] = 0

                status = response.status
                response_data = None

                # Both APIs use JSON as the formatting, so if it doesn't return JSON, then
                # there is an issue with the API itself.
                if response.content_type == "application/json":
                    response_data = await response.json()

                return AIOHTTPResponse(status=status, data=response_data)
        except ClientConnectorError:
            cls._host_failures[host] = cls._host_failures.get(host, 0) + 1

            if cls._host_failures[host] >= cls._max_failures:
                raise ServiceUnavailableError(
                    host,
                    cls._host_failures[host],
                )

            return AIOHTTPResponse(
                status=503,
                data=None,
            )
        except asyncio.TimeoutError:
            cls._host_failures[host] = cls._host_failures.get(host, 0) + 1

            if cls._host_failures[host] >= cls._max_failures:
                raise ServiceUnavailableError(
                    host,
                    cls._host_failures[host],
                )

            return AIOHTTPResponse(
                status=408,
                data=None,
            )
        except ClientConnectionError:
            if cls._reconnecting:
                cls._reconnecting = False
                return AIOHTTPResponse(status=503, data=None)

            cls._reconnecting = True
            cls._session = None
            await cls.init_session()
            result = await cls._request(method, url, headers, data, timeout)
            cls._reconnecting = False
            return result

    @classmethod
    async def get(
        cls,
        url: str,
        headers: dict[str, str] | None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        return await cls._request("GET", url, headers, timeout=timeout)

    @classmethod
    async def post(
        cls,
        url: str,
        headers: dict[str, str] | None,
        data: dict[str, Any] | None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        return await cls._request("POST", url, headers, data=data, timeout=timeout)

    @classmethod
    async def put(
        cls,
        url: str,
        headers: dict[str, str] | None,
        data: dict[str, Any] | None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        return await cls._request("PUT", url, headers, data=data, timeout=timeout)
