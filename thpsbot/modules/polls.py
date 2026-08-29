from datetime import datetime
from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands
from discord.ext import tasks
from discord.ext.commands import Cog

from thpsbot.helpers.auth_helper import is_admin_user
from thpsbot.helpers.config_helper import GUILD_ID, REMINDER_LIST
from thpsbot.helpers.json_helper import JsonHelper
from thpsbot.helpers.poll_helper import (
    BOT_TIMEZONE,
    parse_timestamp,
    replace_end_time,
    summarize_votes,
    truncate_thread_name,
    truncate_title_suffix,
)
from thpsbot.helpers.task_helper import TaskHelper

if TYPE_CHECKING:
    from thpsbot.main import THPSBot

_BAD_TIMESTAMP_HINT = (
    "is not a valid timestamp. Use https://hammertime.cyou for an easier "
    "conversion. Use America/New York as timezone."
)
_MAX_POLL_FAILURES = 5


async def setup(bot: "THPSBot"):
    await bot.add_cog(PollCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="Polls")  # type: ignore


class PrivatePollView(discord.ui.View):
    def __init__(
        self,
        *,
        options: list[str],
        cog: "PollCog",
        votes: dict[str, str] | None = None,
    ) -> None:
        super().__init__(timeout=None)
        self.options = options
        self.cog = cog
        # Votes are keyed by str(user_id) so live state matches what is restored
        # from reminders.json. The metadata shares this exact dict instance.
        self.votes: dict[str, str] = {} if votes is None else votes

        for idx, label in enumerate(options, start=1):
            self.add_item(
                PrivatePollButton(
                    label=label,
                    custom_id=f"priv_poll_btn_{idx}",
                    row=(idx - 1) // 5,
                )
            )

    def record_vote(
        self,
        user_id: int,
        choice: str,
    ) -> str | None:
        """Record a user's vote, returning their previous choice if any.

        Arguments:
            user_id (int): The voting member's Discord id.
            choice (str): The option label they selected.

        Returns:
            prev (str | None): The member's previous choice, or None if new.
        """
        key = str(user_id)
        prev = self.votes.get(key)
        self.votes[key] = choice
        return prev

    def summary(self) -> str:
        """Return the per-option vote tally as display text."""
        return summarize_votes(self.options, self.votes)


class PrivatePollButton(discord.ui.Button):
    def __init__(
        self,
        *,
        label: str,
        custom_id: str,
        row: int,
    ) -> None:
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=custom_id,
            row=row,
        )
        self.choice = label

    async def callback(
        self,
        interaction: Interaction,
    ) -> None:
        """Record the click's vote in shared state, persist it, and confirm."""
        assert isinstance(self.view, PrivatePollView)
        view: PrivatePollView = self.view
        prev = view.record_vote(interaction.user.id, self.choice)

        view.cog.save_reminders()

        poll_message = (
            f"Your vote for **{self.choice}** has been recorded."
            if prev is None
            else f"Vote changed to **{self.choice}** (was **{prev}**)."
        )
        await interaction.response.send_message(
            poll_message,
            ephemeral=True,
        )


class PollCog(Cog, name="Polls", description="Manages THPSBot's polls."):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.reminder_list: dict[str, dict] = REMINDER_LIST
        self.active_private_polls: dict[int, PrivatePollView] = {}

    async def cog_load(self) -> None:
        self.bot.tree.add_command(
            self.poll_group,
            guild=discord.Object(id=GUILD_ID),
            override=True,
        )

        self._check_reminders.start()

        for reminder, metadata in self.reminder_list.items():
            if metadata["type"] == "private":
                view = PrivatePollView(
                    options=metadata["options"],
                    cog=self,
                    votes=metadata["votes"],
                )

                self.bot.add_view(view, message_id=int(reminder))
                self.active_private_polls[int(reminder)] = view

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.poll_group.name,
            guild=discord.Object(id=GUILD_ID),
        )

        self._check_reminders.cancel()

    def save_reminders(self) -> None:
        JsonHelper.save_json(self.reminder_list, "json/reminders.json")

    def _resolve_poll_channel(
        self,
        message_id: str,
    ) -> discord.TextChannel | None:
        """Resolve the text channel a stored poll lives in from its metadata.

        Arguments:
            message_id (str): The poll's message id, a key into the reminder list.

        Returns:
            channel (discord.TextChannel | None): The poll's channel, or None when
                the guild/channel no longer resolves to a text channel.
        """
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return None

        channel = guild.get_channel(int(self.reminder_list[message_id]["channel"]))
        if not isinstance(channel, discord.TextChannel):
            return None

        return channel

    @tasks.loop(seconds=30)
    @TaskHelper.safe_task
    async def _check_reminders(self) -> None:
        await self.reminders()

    async def reminders(self) -> None:
        """Finalize any due polls, DM their reports, and prune them from state."""
        if len(self.reminder_list) == 0:
            return

        current_time = datetime.now(BOT_TIMEZONE)

        remove_polls: list[str] = []
        changed = False
        for reminder, metadata in self.reminder_list.items():
            if metadata["time"] is None:
                remove_polls.append(reminder)
                continue

            poll_time = datetime.fromisoformat(metadata["time"])

            if current_time < poll_time:
                continue

            try:
                author = await self.bot.fetch_user(int(metadata["author"]))
                guild = self.bot.get_guild(GUILD_ID)
                if guild is None:
                    self.bot._log.error(f"Guild {GUILD_ID} not found")
                    continue

                channel = guild.get_channel(int(metadata["channel"]))
                if channel is None or not isinstance(channel, discord.TextChannel):
                    self.bot._log.error(f"Channel {metadata['channel']} not found")
                    continue

                message = await channel.fetch_message(int(reminder))

                embed = message.embeds[0]

                if metadata["type"] == "private":
                    view = self.active_private_polls.pop(int(reminder), None)
                    if view is None:
                        remove_polls.append(reminder)
                        continue
                    report = view.summary()
                    view.stop()
                else:
                    react_counts: dict[str, dict] = {}
                    for reaction in message.reactions:
                        emoji_str = str(reaction.emoji)
                        if emoji_str in metadata["reactions"]:
                            count = reaction.count - (1 if reaction.me else 0)
                            react_counts[emoji_str] = {
                                "name": metadata["reactions"][emoji_str],
                                "count": count,
                            }

                    if not react_counts:
                        report = ""
                    else:
                        lines = [
                            f"{emoji} - {n['name']}: **{n['count']}**"
                            for emoji, n in react_counts.items()
                        ]
                        report = "\n".join(lines)

                    title = embed.title or "Poll"
                    if "(ENDED" not in title:
                        embed.title = truncate_title_suffix(title, " (ENDED)")
                        await message.edit(embed=embed)

                try:
                    await author.send(
                        "Poll Report:\n"
                        + f"[Jump to Poll]({message.jump_url})\n"
                        + "-------------------\n"
                        + f"{report}"
                    )
                    await message.reply(
                        f"Poll is done! Report sent to your DMs, <@{metadata['author']}>!"
                    )
                except discord.errors.Forbidden:
                    await message.reply(
                        f"Poll is done! But, I couldn't send the report, <@{metadata['author']}>!\n"
                        + f"{report}"
                    )

                remove_polls.append(reminder)
            except discord.errors.NotFound:
                self.bot._log.error(f"{reminder} doesn't exist? Removing...")
                if metadata["type"] == "private":
                    self.active_private_polls.pop(int(reminder), None)

                remove_polls.append(reminder)
            except (discord.DiscordServerError, TimeoutError):
                self.bot._log.warning(
                    f"Transient error finalizing poll {reminder}, will retry next loop"
                )
            except Exception:
                self.bot._log.exception(f"Failed to finalize poll {reminder}")
                metadata["failures"] = metadata.get("failures", 0) + 1
                changed = True
                if metadata["failures"] >= _MAX_POLL_FAILURES:
                    self.bot._log.error(
                        f"Removing poll {reminder} after {_MAX_POLL_FAILURES} failures"
                    )
                    if metadata["type"] == "private":
                        self.active_private_polls.pop(int(reminder), None)
                    remove_polls.append(reminder)

        for poll in remove_polls:
            self.reminder_list.pop(poll, None)

        if remove_polls or changed:
            self.save_reminders()

    ###########################################################################
    # poll_group Commands
    ###########################################################################
    poll_group = app_commands.Group(
        name="poll", description="Creates or modifies the behavior of a poll."
    )

    @poll_group.command(
        name="public",
        description="Creates a new public (reaction) poll with up to 5 choices.",
    )
    @app_commands.describe(
        message="Set the message of the poll.",
        time="If used and given a timestamp, will mention you upon time being met.",
        o1_emoji="Emoji for the first option.",
        o1_name="What does this emoji represent for option1?",
        o2_emoji="Emoji for the second option.",
        o2_name="What does this emoji represent for option2?",
        o3_emoji="Emoji for the third option.",
        o3_name="What does this emoji represent for option3?",
        o4_emoji="Emoji for the fourth option.",
        o4_name="What does this emoji represent for option4?",
        o5_emoji="Emoji for the fifth option.",
        o5_name="What does this emoji represent for option5?",
        thread="Automatically create a discussion thread for this poll.",
    )
    async def public_poll(
        self,
        interaction: Interaction,
        message: app_commands.Range[str, 1, 1024],
        time: str | None,
        o1_emoji: app_commands.Range[str, 1, 100],
        o1_name: app_commands.Range[str, 1, 100],
        o2_emoji: app_commands.Range[str, 1, 100],
        o2_name: app_commands.Range[str, 1, 100],
        o3_emoji: app_commands.Range[str, 1, 100] | None,
        o3_name: app_commands.Range[str, 1, 100] | None,
        o4_emoji: app_commands.Range[str, 1, 100] | None,
        o4_name: app_commands.Range[str, 1, 100] | None,
        o5_emoji: app_commands.Range[str, 1, 100] | None,
        o5_name: app_commands.Range[str, 1, 100] | None,
        thread: bool = False,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        local_time: datetime | None = None
        long_tag: str = ""

        if time:
            parsed = parse_timestamp(time)
            if parsed is None:
                await interaction.followup.send(
                    f"{time} {_BAD_TIMESTAMP_HINT}",
                    ephemeral=True,
                )
                return

            local_time, long_tag = parsed
            if local_time <= datetime.now(BOT_TIMEZONE):
                await interaction.followup.send(
                    f"{time} is in the past. Pick a time in the future for the poll to end.",
                    ephemeral=True,
                )
                return

        if interaction.channel is None or not isinstance(
            interaction.channel, discord.TextChannel
        ):
            await interaction.followup.send(
                "This command must be used in a text channel.",
                ephemeral=True,
            )
            return

        options: list[tuple[str | None, str | None]] = [
            (o1_emoji, o1_name),
            (o2_emoji, o2_name),
            (o3_emoji, o3_name),
            (o4_emoji, o4_name),
            (o5_emoji, o5_name),
        ]

        reactions: dict[str, str] = {}
        labeler: list[str] = []
        for emoji, name in options:
            if emoji is None:
                continue

            if emoji in reactions:
                await interaction.followup.send(
                    f"{emoji} is used by more than one option. Give each option a unique emoji.",
                    ephemeral=True,
                )
                return

            label = name or "---"
            reactions[emoji] = label
            labeler.append(f"{emoji} = **{label}**")

        # Build the full description up front so posting is a single send; only the
        # thread-link edit remains (it needs the thread's jump_url).
        parts: list[str] = [f"**{message}**"]
        if time:
            parts.append(f"This poll ends at {long_tag}!")
        parts.append("\n".join(labeler))
        description = "\n\n".join(parts)

        embed = discord.Embed(title="Poll", description=description)
        poll = await interaction.channel.send(embed=embed)

        # Reactions are added after posting, so an invalid emoji only fails here.
        try:
            for emoji in reactions:
                await poll.add_reaction(emoji)
        except discord.HTTPException:
            # Covers both an invalid emoji (400) and missing reaction perms (403).
            await poll.delete()
            await interaction.followup.send(
                f"Couldn't react with {emoji} (invalid emoji, or I lack permission). "
                + "The poll was cancelled.",
                ephemeral=True,
            )
            return

        if thread:
            discussion = await poll.create_thread(name=truncate_thread_name(message))
            embed.description = f"{description}\n\n[Discussion]({discussion.jump_url})"
            await poll.edit(embed=embed)

        if time:
            self.reminder_list[str(poll.id)] = {
                "type": "public",
                "time": str(local_time),
                "channel": interaction.channel.id,
                "author": interaction.user.id,
                "reactions": reactions,
            }
            self.save_reminders()

            await interaction.followup.send(
                "Poll created successfully!\n"
                + f"Use `/poll edit {poll.id}` to modify the time if needed!",
                ephemeral=True,
            )
        else:
            # Timeless polls aren't tracked, so /poll edit can't manage them.
            await interaction.followup.send(
                "Poll created successfully!",
                ephemeral=True,
            )

    @poll_group.command(
        name="private",
        description="Creates a new private (button) poll with up to 5 choices.",
    )
    @app_commands.describe(
        message="Set the message of the poll.",
        time="Time when the poll will be completed.",
        option1="What do you want to call the first option?",
        option2="What do you want to call the second option?",
        option3="What do you want to call the third option?",
        option4="What do you want to call the fourth option?",
        option5="What do you want to call the fifth option?",
        thread="Automatically create a discussion thread for this poll.",
    )
    async def private_poll(
        self,
        interaction: Interaction,
        message: app_commands.Range[str, 1, 1024],
        time: str,
        option1: app_commands.Range[str, 1, 80],
        option2: app_commands.Range[str, 1, 80],
        option3: app_commands.Range[str, 1, 80] | None,
        option4: app_commands.Range[str, 1, 80] | None,
        option5: app_commands.Range[str, 1, 80] | None,
        thread: bool = True,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        parsed = parse_timestamp(time)
        if parsed is None:
            await interaction.followup.send(
                f"{time} {_BAD_TIMESTAMP_HINT}",
                ephemeral=True,
            )
            return

        local_time, long_tag = parsed
        if local_time <= datetime.now(BOT_TIMEZONE):
            await interaction.followup.send(
                f"{time} is in the past. Pick a time in the future for the poll to end.",
                ephemeral=True,
            )
            return

        options_content = [
            o for o in (option1, option2, option3, option4, option5) if o
        ]

        # Votes are counted by label, so duplicate labels would silently merge.
        if len(set(options_content)) != len(options_content):
            await interaction.followup.send(
                "Two options share the same label. Give each option a unique name.",
                ephemeral=True,
            )
            return

        if interaction.channel is None or not isinstance(
            interaction.channel, discord.TextChannel
        ):
            await interaction.followup.send(
                "This command must be used in a text channel.",
                ephemeral=True,
            )
            return

        # Share one votes dict between the view and the reminder metadata so votes
        # recorded by the buttons survive the reminders loop's periodic saves.
        votes: dict[str, str] = {}
        view = PrivatePollView(options=options_content, cog=self, votes=votes)

        description = f"**{message}**\n\nThis poll ends at {long_tag}!"
        embed = discord.Embed(title="Poll", description=description)
        poll = await interaction.channel.send(embed=embed, view=view)

        if thread:
            discussion = await poll.create_thread(name=truncate_thread_name(message))
            embed.description = f"{description}\n\n[Discussion]({discussion.jump_url})"
            await poll.edit(embed=embed)

        self.active_private_polls[poll.id] = view

        self.reminder_list[str(poll.id)] = {
            "type": "private",
            "time": str(local_time),
            "channel": interaction.channel.id,
            "author": interaction.user.id,
            "options": options_content,
            "votes": votes,
        }

        self.save_reminders()

        await interaction.followup.send(
            "Poll created successfully!\n"
            + f"Use `/poll edit {poll.id}` to modify the time if needed!",
            ephemeral=True,
        )

    @poll_group.command(
        name="edit",
        description="Edits a poll's end time/date.",
    )
    @app_commands.describe(
        message_id="Message ID of the poll being modified.",
        time="Changes the message's poll end time/date to what is given. Use hammertime.cyou!",
    )
    async def edit_poll(
        self,
        interaction: Interaction,
        message_id: str,
        time: str,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not await is_admin_user(interaction.user, self.bot):
            raise app_commands.CheckFailure

        try:
            message_int = int(message_id)
        except ValueError:
            await interaction.followup.send(
                f"{message_id} is invalid - it must be a message ID number.",
                ephemeral=True,
            )
            return

        parsed = parse_timestamp(time)
        if parsed is None:
            await interaction.followup.send(
                f"{time} {_BAD_TIMESTAMP_HINT}",
                ephemeral=True,
            )
            return

        local_time, long_tag = parsed
        if local_time <= datetime.now(BOT_TIMEZONE):
            await interaction.followup.send(
                f"{time} is in the past. Pick a time in the future for the poll to end.",
                ephemeral=True,
            )
            return

        if message_id not in self.reminder_list:
            await interaction.followup.send(
                f"{message_id} is not in the polls list.",
                ephemeral=True,
            )
            return

        channel = self._resolve_poll_channel(message_id)
        if channel is None:
            await interaction.followup.send(
                f"The channel for poll {message_id} no longer exists.",
                ephemeral=True,
            )
            return

        try:
            message = await channel.fetch_message(message_int)
        except discord.NotFound:
            await interaction.followup.send(
                f"{message_id} does not exist. Was it deleted?",
                ephemeral=True,
            )
            return

        embed = message.embeds[0]

        if embed.description is None:
            await interaction.followup.send(
                f"{message_id} has no description to edit.",
                ephemeral=True,
            )
            return

        embed.description = replace_end_time(embed.description, long_tag)
        await message.edit(embed=embed)

        self.reminder_list[message_id]["time"] = str(local_time)

        self.save_reminders()

        await interaction.followup.send(
            f"{time} is the new end time/date for that poll!",
            ephemeral=True,
        )

    @poll_group.command(
        name="stop",
        description="Force stops a poll early.",
    )
    @app_commands.describe(
        message_id="Message ID of the poll being modified.",
    )
    async def stop_poll(
        self,
        interaction: Interaction,
        message_id: str,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not await is_admin_user(interaction.user, self.bot):
            raise app_commands.CheckFailure

        try:
            message_int = int(message_id)
        except ValueError:
            await interaction.followup.send(
                f"{message_id} is invalid - it must be a message ID number.",
                ephemeral=True,
            )
            return

        if message_id not in self.reminder_list:
            await interaction.followup.send(
                f"{message_id} is not in the polls list.",
                ephemeral=True,
            )
            return

        channel = self._resolve_poll_channel(message_id)
        if channel is None:
            await interaction.followup.send(
                f"The channel for poll {message_id} no longer exists.",
                ephemeral=True,
            )
            return

        try:
            message = await channel.fetch_message(message_int)
        except discord.NotFound:
            await interaction.followup.send(
                f"{message_int} does not exist. Was it deleted?",
                ephemeral=True,
            )
            return

        local_time = datetime.now(BOT_TIMEZONE)
        long_tag = f"<t:{int(local_time.timestamp())}:F>"

        embed = message.embeds[0]

        if embed.description:
            embed.description = replace_end_time(embed.description, long_tag)
        embed.title = truncate_title_suffix(embed.title or "Poll", " (ENDED EARLY)")
        await message.edit(embed=embed)

        self.reminder_list[message_id]["time"] = str(local_time)
        await self._check_reminders()

        await interaction.followup.send(
            f"{message_id}'s poll was stopped. DM should be sent to author shortly.",
            ephemeral=True,
        )
