import functools
from typing import Any, Callable, TypeVar

import discord
import sentry_sdk
from discord.ext.commands.errors import CommandNotFound

F = TypeVar("F", bound=Callable[..., Any])


class TaskHelper:
    @staticmethod
    def safe_task(func: F) -> F:
        """Custom decorator that handles common errors within Discord.py.

        Exceptions:
            DiscordServerError: Warning log, retry next loop.
            TimeoutError: Warning log, retry next loop.
            CommandNotFound: Warning log.
        """

        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            task_name = func.__name__
            try:
                return await func(self, *args, **kwargs)
            except discord.DiscordServerError:
                self.bot._log.warning(
                    f"Discord Server Error 503: {task_name}, will retry next loop"
                )
            except TimeoutError:
                self.bot._log.warning(
                    f"Timeout Error: {task_name}, will retry next loop"
                )
            except CommandNotFound:
                self.bot._log.warning(f"Command Not Found: {task_name}.")
            except Exception as e:
                self.bot._log.exception(f"Unexpected error in {task_name}")
                sentry_sdk.capture_exception(e)

        return wrapper  # type: ignore
