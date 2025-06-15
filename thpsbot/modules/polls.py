import re
import zoneinfo
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands
from discord.ext import tasks
from discord.ext.commands import Cog

from thpsbot.helpers.auth_helper import is_admin_user
from thpsbot.helpers.config_helper import GUILD_ID, REMINDER_LIST
from thpsbot.helpers.json_helper import JsonHelper

if TYPE_CHECKING:
    from main import THPSBot


async def setup(bot: "THPSBot"):
    await bot.add_cog(PollCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="Polls")


class PrivatePollView(discord.ui.View):
    def __init__(
        self, *, options: list[str], votes: dict[int, str] | None = None
    ) -> None:
        super().__init__(timeout=None)
        self.options = options
        self.votes: dict[int, str] = votes or {}

        for idx, label in enumerate(options, start=1):
            cid = f"priv_poll_btn_{idx}"
            self.add_item(
                PrivatePollButton(
                    label=label,
                    custom_id=cid,
                    row=(idx - 1) // 5,
                )
            )

    def summary(self) -> str:
        counts = {opt: 0 for opt in self.options}
        for choice in self.votes.values():
            counts[choice] += 1
        return "\n".join(f"**{opt}** - {n}" for opt, n in counts.items())


class PrivatePollButton(discord.ui.Button):
    def __init__(self, *, label: str, custom_id: str, row: int):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=custom_id,
            row=row,
        )
        self.choice = label

    async def callback(self, interaction: Interaction):
        view: PrivatePollView = self.view
        uid = interaction.user.id
        choice = self.label
        prev = view.votes.get(uid)
        view.votes[uid] = choice

        store: dict[dict, str] = JsonHelper.load_json("json/reminders.json")
        poll_data = store.get(str(interaction.message.id))
        if poll_data:
            poll_data["votes"][str(uid)] = choice
            JsonHelper.save_json(store, "json/reminders.json")

        poll_message = (
            f"Your vote for **{choice}** has been recorded."
            if prev is None
            else f"Vote changed to **{choice}** (was **{prev}**)."
        )
        await interaction.response.send_message(
            poll_message,
            ephemeral=True,
        )


class PollCog(Cog, name="Polls", description="Manages THPSBot's polls."):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.reminder_list: dict[dict, str] = REMINDER_LIST
        self.active_private_polls: dict[int, PrivatePollView] = {}

    async def cog_load(self) -> None:
        self.bot.tree.add_command(
            self.poll_group,
            guild=discord.Object(id=GUILD_ID),
            override=True,
        )

        self.check_reminders.start()

        for reminder, metadata in self.reminder_list.items():
            if metadata["type"] == "private":
                view = PrivatePollView(
                    options=metadata["options"],
                    votes=metadata["votes"],
                )

                self.bot.add_view(view, message_id=int(reminder))
                self.active_private_polls[int(reminder)] = view

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.poll_group,
            type=app_commands.Group,
            guild=discord.Object(id=GUILD_ID),
        )

        self.check_reminders.cancel()

    @tasks.loop(seconds=30)
    async def check_reminders(self) -> None:
        if len(self.reminder_list) == 0:
            return

        current_time = datetime.now(zoneinfo.ZoneInfo("America/New_York"))

        remove_polls = []
        for reminder, metadata in self.reminder_list.items():
            poll_time = datetime.fromisoformat(metadata["time"])

            if current_time < poll_time:
                return

            try:
                author = await self.bot.fetch_user(int(metadata["author"]))
                guild: discord.Guild = self.bot.get_guild(GUILD_ID)
                channel = guild.get_channel(int(metadata["channel"]))
                message = await channel.fetch_message(int(reminder))

                embed = message.embeds[0]

                if metadata["type"] == "private":
                    view = self.active_private_polls.pop(int(reminder), None)
                    report = view.summary()
                    view.stop()
                else:
                    react_counts: dict[dict, str] = {}
                    for reaction in message.reactions:
                        if reaction.emoji in self.reminder_list[reminder]["reactions"]:
                            count = reaction.count - (1 if reaction.me else 0)
                            react_counts[reaction.emoji] = {
                                "name": self.reminder_list[reminder]["reactions"][
                                    reaction.emoji
                                ],
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

                    embed.title = embed.title + " (ENDED)"
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
            except AttributeError as e:
                self.bot._log.error(e)

        for poll in remove_polls:
            self.reminder_list.pop(poll, None)

        JsonHelper.save_json(self.reminder_list, "json/reminders.json")

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
        option1="Emoji for the first option.",
        option1_name="What does this emoji represent for option1?",
        option2="Emoji for the second option.",
        option2_name="What does this emoji represent for option2?",
        option3="Emoji for the third option.",
        option3_name="What does this emoji represent for option3?",
        option4="Emoji for the fourth option.",
        option4_name="What does this emoji represent for option4?",
        option5="Emoji for the fifth option.",
        option5_name="What does this emoji represent for option5?",
    )
    async def public_poll(
        self,
        interaction: Interaction,
        message: str,
        time: str,
        option1: str,
        option1_name: str,
        option2: str,
        option2_name: str,
        option3: str | None,
        option3_name: str | None,
        option4: str | None,
        option4_name: str | None,
        option5: str | None,
        option5_name: str | None,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        if time:
            matched_time = re.match(r"<t:(\d+):[a-zA-Z]?>", time)
            if not matched_time:
                await interaction.followup.send(
                    f"{time} is not a valid timestamp. Use https://hammertime.cyou "
                    + "for an easier conversion. Use America/New York as timezone.",
                    ephemeral=True,
                )
                return

            timestamp = int(matched_time.group(1))
            utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            local_time = utc_dt.astimezone(zoneinfo.ZoneInfo("America/New_York"))
            long_tag = f"<t:{timestamp}:F>"
        else:
            local_time = None

        poll = await interaction.channel.send(
            embed=discord.Embed(
                title=f"Poll: {message}",
            ),
        )
        embed = poll.embeds[0]

        options: list[tuple[str | None, str | None]] = [
            (option1, option1_name),
            (option2, option2_name),
            (option3, option3_name),
            (option4, option4_name),
            (option5, option5_name),
        ]

        labeler: list = []
        reactions: dict[dict, str] = {}
        for emoji, label in options:
            if emoji is None:
                continue

            await poll.add_reaction(emoji)

            label = label or "---"
            reactions[emoji] = label
            labeler.append(f"{emoji} = **{label}**\n")

        if time:
            embed.description = f"This poll ends at {long_tag}!\n"

        embed.description = embed.description + "\n".join(labeler)
        await poll.edit(embed=embed)

        self.reminder_list.update(
            {
                str(poll.id): {
                    "type": "public",
                    "time": str(local_time),
                    "channel": interaction.channel.id,
                    "author": interaction.user.id,
                    "reactions": reactions,
                }
            }
        )

        JsonHelper.save_json(self.reminder_list, "json/reminders.json")

        await interaction.followup.send(
            "Poll created successfully!\n"
            + f"Use `/poll edit {poll.id}` to modify the time if needed!",
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
    )
    async def private_poll(
        self,
        interaction: Interaction,
        message: str,
        time: str,
        option1: str,
        option2: str,
        option3: str | None,
        option4: str | None,
        option5: str | None,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        matched_time = re.match(r"<t:(\d+):[a-zA-Z]?>", time)
        if not matched_time:
            await interaction.followup.send(
                f"{time} is not a valid timestamp. Use https://hammertime.cyou "
                + "for an easier conversion. Use America/New York as timezone.",
                ephemeral=True,
            )
            return

        timestamp = int(matched_time.group(1))
        utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        local_time = utc_dt.astimezone(zoneinfo.ZoneInfo("America/New_York"))
        long_tag = f"<t:{timestamp}:F>"

        options: list = [option1, option2, option3, option4, option5]
        options_content = [option for option in options if option]

        view = PrivatePollView(options=options_content)

        poll = await interaction.channel.send(
            embed=discord.Embed(
                title=f"Poll: {message}",
            ),
            view=view,
        )
        embed = poll.embeds[0]

        if time:
            embed.description = f"The poll ends at {long_tag}!\n"
            await poll.edit(embed=embed)

        self.active_private_polls[int(poll.id)] = view

        self.reminder_list.update(
            {
                str(poll.id): {
                    "type": "private",
                    "time": str(local_time),
                    "channel": interaction.channel.id,
                    "author": interaction.user.id,
                    "options": options_content,
                    "votes": {},
                }
            }
        )

        JsonHelper.save_json(self.reminder_list, "json/reminders.json")

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
        time="Changes the message's poll end time/date to what is given.",
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
                f"{message_id} is invalid - it must be a channel ID number.",
                ephemeral=True,
            )
            return

        matched_time = re.match(r"<t:(\d+):[a-zA-Z]?>", time)
        if not matched_time:
            await interaction.followup.send(
                f"{time} is not a valid timestamp. Use https://hammertime.cyou "
                + "for an easier conversion. Use America/New York as timezone.",
                ephemeral=True,
            )
            return

        timestamp = int(matched_time.group(1))
        utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        local_time = utc_dt.astimezone(zoneinfo.ZoneInfo("America/New_York"))
        long_tag = f"<t:{timestamp}:F>"

        if message_id not in self.reminder_list:
            await interaction.followup.send(
                f"{message_id} is not in the polls list.",
                ephemeral=True,
            )
            return

        message_id = await interaction.channel.fetch_message(int(message_int))

        if not message_id:
            await interaction.followup.send(
                f"{message_id} does not exist. Is it in this channel or was it deleted?",
                ephemeral=True,
            )
            return

        embed = message_id.embeds[0]
        edited_description = re.sub(
            r"This poll ends at <t:\d+:[A-Za-z]?>",
            f"This poll ends at {long_tag} (updated)",
            embed.description,
            flags=re.MULTILINE,
        )

        embed.description = edited_description
        await message_id.edit(embed=embed)

        self.reminder_list[message_id].update({"time": str(local_time)})

        JsonHelper.save_json(self.reminder_list, "json/reminders.json")

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
                f"{message_id} is invalid - it must be a channel ID number.",
                ephemeral=True,
            )
            return

        message = await interaction.channel.fetch_message(message_int)

        if not message_id:
            await interaction.followup.send(
                f"{message_int} does not exist. Is it in this channel or was it deleted?",
                ephemeral=True,
            )
            return

        local_time = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
        long_tag = f"<t:{int((local_time).timestamp())}:F>"

        embed = message.embeds[0]

        edited_description = re.sub(
            r"This poll ends at <t:\d+:[A-Za-z]?>",
            f"This poll ends at {long_tag} (updated)",
            embed.description,
            flags=re.MULTILINE,
        )
        embed.description = edited_description
        embed.title = f"{embed.title} (ENDED EARLY)"
        await message.edit(embed=embed)

        self.reminder_list[message].update({"time": str(local_time)})
        await self.check_reminders()

        await interaction.followup.send(
            f"{message}'s poll was stopped. DM should be sent to author shortly.",
            ephemeral=True,
        )
