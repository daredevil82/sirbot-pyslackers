import json
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)


def create_endpoints(plugin):
    plugin.on_command("/admin", tell_admin)
    plugin.on_command("/how-to-ask", ask)
    plugin.on_command("/gif", gif_search)
    plugin.on_command("/pypi", pypi_search)
    plugin.on_command("/sponsors", sponsors)
    plugin.on_command("/snippet", snippet)
    plugin.on_command("/report", report)
    plugin.on_command("/save", save_conversation)


async def ask(command, app):
    slack = app.plugins["slack"]
    response = Message()
    response["channel"] = command["channel_id"]
    response["unfurl_links"] = False
    
    response.text = (
        "Knowing how to ask a good question is a highly invaluable skill that will benefit you greatly in any career. "
        "<https://stackoverflow.com/help/how-to-ask> is a good collection of suggestions and strategies to help you "
        "structure and prase your question to make it easier for those here to understand your problem and "
        "help you work to a solution."
    )
    
    await slack.api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def sponsors(command, app):
    slack = app.plugins["slack"]
    response = Message()
    response["channel"] = command["channel_id"]
    response["unfurl_links"] = False

    response["text"] = (
        "Thanks to our sponsors, <https://digitalocean.com|Digital Ocean> and "
        "<https://sentry.io|Sentry> for providing hosting & services helping us "
        "host our <https://www.pyslackers.com|website> and Sir Bot-a-lot.\n"
        "If you are planning on using one of those services please use our referral codes: \n"
        "1. <https://m.do.co/c/457f0988c477|Digital Ocean referral code>\n"
        "2. <https://sentry.io/?utm_source=referral&utm_content=pyslackers&utm_campaign=community|"
        "Sentry referral code>."
    )

    await slack.api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def report(command, app):

    data = {
        "trigger_id": command["trigger_id"],
        "dialog": {
            "callback_id": "report",
            "title": "Report user",
            "elements": [
                {
                    "label": "Offending user",
                    "name": "user",
                    "type": "select",
                    "data_source": "users",
                },
                {
                    "label": "Channel",
                    "name": "channel",
                    "type": "select",
                    "data_source": "channels",
                    "optional": True,
                },
                {
                    "label": "Comment",
                    "name": "comment",
                    "type": "textarea",
                    "value": command["text"],
                },
            ],
        },
    }

    await app.plugins["slack"].api.query(url=methods.DIALOG_OPEN, data=data)


async def gif_search(command, app):
    response = Message()
    response["channel"] = command["channel_id"]

    if command["text"]:
        response["user"] = command["user_id"]
        urls = await app.plugins["giphy"].search(command["text"])

        if urls:
            urls = [url.split("?")[0] for url in urls]
            data = json.dumps({"urls": urls, "search": command["text"], "index": 0})

            response["attachments"] = [
                {
                    "title": f'You searched for `{command["text"]}`',
                    "fallback": f'You searched for `{command["text"]}`',
                    "image_url": urls[0],
                    "callback_id": "gif_search",
                    "actions": [
                        {
                            "name": "ok",
                            "text": "Send",
                            "style": "primary",
                            "value": data,
                            "type": "button",
                        },
                        {
                            "name": "next",
                            "text": "Next",
                            "value": data,
                            "type": "button",
                        },
                        {
                            "name": "cancel",
                            "text": "Cancel",
                            "style": "danger",
                            "value": data,
                            "type": "button",
                        },
                    ],
                }
            ]
        else:
            response["text"] = f'No result found on giphy for: `{command["text"]}`'
        await app.plugins["slack"].api.query(
            url=methods.CHAT_POST_EPHEMERAL, data=response
        )

    else:
        url = await app.plugins["giphy"].trending()

        response["attachments"] = [
            {
                "title": "Trending gif on Giphy",
                "fallback": "Trending gif on Giphy",
                "image_url": url,
            }
        ]

        await app.plugins["slack"].api.query(
            url=methods.CHAT_POST_MESSAGE, data=response
        )


async def pypi_search(command, app):
    response = Message()
    response["channel"] = command["channel_id"]

    if not command["text"]:
        response["response_type"] = "ephemeral"
        response["text"] = "Please enter the package name you wish to find"
    else:
        results = await app.plugins["pypi"].search(command["text"])
        if results:
            response["response_type"] = "in_channel"
            response["attachments"] = [
                {
                    "title": f'<@{command["user_id"]}> Searched PyPi for `{command["text"]}`',
                    "fallback": f'Pypi search of {command["text"]}',
                    "fields": [],
                }
            ]

            for result in results[:3]:
                response["attachments"][0]["fields"].append(
                    {
                        "title": result["name"],
                        "value": f'<{app.plugins["pypi"].PROJECT_URL.format(result["name"])}|{result["summary"]}>',
                    }
                )

            if len(results) == 4:
                response["attachments"][0]["fields"].append(
                    {
                        "title": results[3]["name"],
                        "value": f'<{app.plugins["pypi"].PROJECT_URL.format(results[3]["name"])}|{results[3]["summary"]}>',
                    }
                )
            elif len(results) > 3:
                response["attachments"][0]["fields"].append(
                    {
                        "title": f"More results",
                        "value": f'<{app.plugins["pypi"].RESULT_URL.format(command["text"])}|'
                        f"{len(results) - 3} more results..>",
                    }
                )

        else:
            response["response_type"] = "ephemeral"
            response[
                "text"
            ] = f"Could not find anything on PyPi matching `{command['text']}`"

    await app.plugins["slack"].api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def snippet(command, app):
    response = Message()
    response["channel"] = command["channel_id"]
    response["unfurl_links"] = False

    response["text"] = (
        "Please use the snippet feature, or backticks, when sharing code. You can do so by "
        "clicking on the :heavy_plus_sign: on the left of the input box for a snippet.\n"
        "For more information on snippets click "
        "<https://get.slack.help/hc/en-us/articles/204145658-Create-a-snippet|here>.\n"
        "For more information on inline code formatting with backticks click "
        "<https://get.slack.help/hc/en-us/articles/202288908-Format-your-messages#inline-code|here>."
    )

    await app.plugins["slack"].api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def tell_admin(command, app):

    data = {
        "trigger_id": command["trigger_id"],
        "dialog": {
            "callback_id": "tell_admin",
            "title": "Message the admin team",
            "elements": [
                {
                    "label": "Message",
                    "name": "message",
                    "type": "textarea",
                    "value": command["text"],
                }
            ],
        },
    }

    await app.plugins["slack"].api.query(url=methods.DIALOG_OPEN, data=data)


async def save_conversation(command, app):

    data = {
        "trigger_id": command["trigger_id"],
        "dialog": {
            "callback_id": "save_conversation",
            "title": "Save conversation",
            "elements": [
                {
                    "label": "Title",
                    "name": "title",
                    "type": "text",
                    "value": command["text"],
                },
                {
                    "label": "Channel",
                    "name": "channel",
                    "type": "select",
                    "value": command["channel_id"],
                    "data_source": "channels",
                },
                {
                    "label": "Start",
                    "name": "start",
                    "type": "select",
                    "options": [
                        {"label": "2 minutes ago", "value": 2 * 60},
                        {"label": "5 minutes ago", "value": 5 * 60},
                        {"label": "10 minutes ago", "value": 10 * 60},
                        {"label": "15 minutes ago", "value": 15 * 60},
                        {"label": "20 minutes ago", "value": 20 * 60},
                        {"label": "25 minutes ago", "value": 25 * 60},
                        {"label": "30 minutes ago", "value": 30 * 60},
                    ],
                },
                {
                    "label": "End",
                    "name": "end",
                    "type": "select",
                    "options": [
                        {"label": "now", "value": 0},
                        {"label": "2 minutes ago", "value": 2 * 60},
                        {"label": "5 minutes ago", "value": 5 * 60},
                        {"label": "10 minutes ago", "value": 10 * 60},
                        {"label": "15 minutes ago", "value": 15 * 60},
                        {"label": "20 minutes ago", "value": 20 * 60},
                        {"label": "25 minutes ago", "value": 25 * 60},
                    ],
                },
                {
                    "label": "Comment",
                    "name": "comment",
                    "type": "textarea",
                    "value": command["text"],
                    "optional": True,
                },
            ],
        },
    }

    await app.plugins["slack"].api.query(url=methods.DIALOG_OPEN, data=data)
