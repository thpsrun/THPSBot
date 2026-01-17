from dataclasses import dataclass
from typing import Any

import aiohttp


@dataclass
class AIOHTTPResponse:
    status: int
    data: Any | None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class AIOHTTPHelper:
    _session: aiohttp.ClientSession | None = None

    @classmethod
    async def init_session(cls) -> None:
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession()

    @classmethod
    async def close_session(cls) -> None:
        if cls._session and not cls._session.closed:
            await cls._session.close()

    @classmethod
    async def get(
        cls, url: str, headers: dict[str, str] | None, timeout: int = 10
    ) -> AIOHTTPResponse:
        if cls._session is None or cls._session.closed:
            await cls.init_session()

        assert cls._session is not None
        async with cls._session.get(url, headers=headers, timeout=timeout) as response:
            status = response.status
            data = None
            if response.content_type == "application/json":
                data = await response.json()
            else:
                data = await response.read()
            return AIOHTTPResponse(status=status, data=data)

    @staticmethod
    async def post(
        url: str,
        headers: dict[str, str] | None,
        data: dict[str, Any] | None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=data, headers=headers, timeout=timeout
            ) as response:
                status = response.status
                response_data = None

                if response.content_type == "application/json":
                    response_data = await response.json()

                return AIOHTTPResponse(status=status, data=response_data)

    @staticmethod
    async def put(
        url: str,
        headers: dict[str, str] | None,
        data: dict[str, Any] | None,
        timeout: int = 10,
    ) -> AIOHTTPResponse:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url, json=data, headers=headers, timeout=timeout
            ) as response:
                status = response.status
                response_data = None

                if response.content_type == "application/json":
                    response_data = await response.json()

                return AIOHTTPResponse(status=status, data=response_data)
