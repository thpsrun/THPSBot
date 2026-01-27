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
    async def get(
        cls,
        url: str,
        headers: dict[str, str] | None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        if cls._session is None or cls._session.closed:
            await cls.init_session()

        assert cls._session is not None
        host = cls._extract_host(url)

        try:
            async with cls._session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                cls._host_failures[host] = 0

                status = response.status
                data = None
                if response.content_type == "application/json":
                    data = await response.json()
                else:
                    data = await response.read()
                return AIOHTTPResponse(status=status, data=data)
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
        except ClientConnectionError:
            if cls._reconnecting:
                cls._reconnecting = False
                return AIOHTTPResponse(status=503, data=None)

            cls._reconnecting = True
            cls._session = None
            await cls.init_session()
            result = await cls.get(url, headers, timeout)
            cls._reconnecting = False
            return result

    @staticmethod
    async def post(
        url: str,
        headers: dict[str, str] | None,
        data: dict[str, Any] | None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                status = response.status
                response_data = None

                if response.content_type == "application/json":
                    response_data = await response.json()

                return AIOHTTPResponse(
                    status=status,
                    data=response_data,
                )

    @staticmethod
    async def put(
        url: str,
        headers: dict[str, str] | None,
        data: dict[str, Any] | None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                status = response.status
                response_data = None

                if response.content_type == "application/json":
                    response_data = await response.json()

                return AIOHTTPResponse(
                    status=status,
                    data=response_data,
                )
