### BOT GROUP:
This group of commands is mostly to modify the functionality of the bot.

`/bot ping` (ADMIN)
- Checks to see if the bot is responding.

`/bot reload` (ADMIN)
- Reloads most of the bot's functions; use this if something is acting funky.

`/bot status <action> <status> <force>` (ADMIN)
- Action: Add, remove, or force a particular status.
    - When Add is used, `status` is required.
    - When Remove is used, `status` is required.
    - When Force is used, `status` is NOT used.
- Status: Sets or removes the status from the bot's status table.
- Force: When True and used with the Add action, it will force the bot to change to this automatically.

`/bot pfp <action> <img_url> <pfp>` (ADMIN)
- Action: Add or force a particular profile picture.
    - When Add is used, `img_url` is required.
    - When Force is used, `img_url` is NOT used. `pfp` can be used to choose the picture you want.
- Img_url: When Add is used, this is the complete URL of an image you want added to the bot.
- Pfp: When used with the Force action, this lets you choose the profile picture you want. If nothing is set, it is random.
---
### REACTION GROUP:
This group of commands help with setting up reactions on message that, when pressed, will give users a specific role.
`/reaction message <action> <message> <emoji> <role>` (ADMIN)
- Action: Set or remove a reaction from a message.
    - When Add is used, `message`, `emoji`, and `role` are required.
    - When Remove is used, `message` is required; `emoji` OR `role` is required.
- Message: The message ID that will be reacted.
- Emoji: The emoji you want to use for the reaction.
- Role: The role you want assigned to the reaction.
---
### POLL GROUP:
This group of commands is used to create polls. Public polls use reactions to tally results (multi-choice is allowed); private polls use buttons to tally results (multi-choice is not allowed).
`/poll public <message> <time> <option1> <option1_name> <option2> <option2_name> <option3> <option3_name> <option4> <option4_name> <option5> <option5_name>`
- Message: The message you want to set for the poll.
- Time: When the set time is hit, the author is mentioned and a report is sent via DM to them. Use <https://hammertime.cyou>.
- Option1-5: Set the emoji you want to use for each emoji.
- Option1-5_name: Set what the reaction actually means. It appears on the bot.

`/poll private <message> <time> <option1> <option2> <option3> <option4> <option5>`
- Message: The message you want to set for the poll.
- Time: When the set time is hit, the author is mentioned and a report is sent via DM to them. Use <https://hammertime.cyou>.
- Option1-5: The name of the buttons that will appear.

`/poll edit <message_id> <time>` (ADMIN)
- Message_ID: The message ID of which you want to modify the time.
- Time: Modify when the author will be mentioned and a report send to them via DM. Use <https://hammertime.cyou>.

`/poll stop <message_id>` (ADMIN)
- Message_ID: Force stops the poll you select. Report will be sent via DM.
---
### STREAM GROUP:
This group of commands sets the games that the bot will look up from the Twitch API.
`/stream game <action> <name>` (ADMIN)
- Action: Add a game to the stream lookup table.
- Name: Exact name of the game to be added.
---
### THPS.RUN GROUP:
This group of commands is used to interact with the thps.run API.
`/thpsrun player <action> <name> <ex_stream>`
- Action:
    - Show is used to create an embed with thps.run information about a player. (ALL USERS)
    - Update is used to force sync a player's information on thps.run with Speedrun.com. (ADMIN)
- Name: The exact speedrun.com name of the player to be synced or updated.
- Ex_stream: Optional. If True, the player is exempted from appearing in the livestream channel.

`/thpsrun run <action> <url>`
- Action:
    - Show is used to create an embed of that specific run, using thps.run information. (ALL RUNS)
    - Import is used to force sync a run from Speedrun.com to thps.run (e.g., you need to update metadata, video is wrong, etc.) (ADMIN)
- URL: The Speedrun.com URL (or run ID) of the run being shown or updated.
