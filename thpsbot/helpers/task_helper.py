import functools
from typing import Any, Callable, TypeVar

import discord
import sentry_sdk

F = TypeVar("F", bound=Callable[..., Any])


class TaskHelper:
    """Provides utilities for Discord background tasks."""

    @staticmethod
    def safe_task(func: F) -> F:
        """
        Decorator for discord.ext.tasks loops that handles common errors.

        - DiscordServerError and TimeoutError: warning log, retry next loop
        - Other exceptions: error log + Sentry report

        Usage:
            @tasks.loop(minutes=1)
            @TaskHelper.safe_task
            async def my_task(self) -> None:
                await self._my_task_impl()

        Note: The decorated method must be a cog method with self.bot._log available.
        """

        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            task_name = func.__name__
            try:
                return await func(self, *args, **kwargs)
            except discord.DiscordServerError:
                self.bot._log.warning(
                    f"Discord 503 error in {task_name}, will retry next loop"
                )
            except TimeoutError:
                self.bot._log.warning(
                    f"Timeout error in {task_name}, will retry next loop"
                )
            except Exception as e:
                self.bot._log.exception(f"Unexpected error in {task_name}")
                sentry_sdk.capture_exception(e)

        return wrapper  # type: ignore[return-value]
