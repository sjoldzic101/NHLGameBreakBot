#!/usr/bin/env python3.6
import discord
import asyncio
import sys
import string
import importlib
import nhl_gamebreak_lib as nhlgb
from asynccmd import Cmd
from contextlib import suppress
from pathlib import Path
import os

os.environ['TZ'] = 'America/New_York'

client = discord.Client()

#exec_get = None
console_mode = False
param_send_to_discord = False
games_url = "http://nhl-score-api.herokuapp.com/api/scores/latest"
for arg in sys.argv:
        if arg == "--console":
            console_mode = True
            continue
        if arg == "--send-to-discord":
            param_send_to_discord = True
            continue
        if "--url=" in arg:
            games_url = arg.split('=')[1]

            if games_url == "testing":
                games_url = "http://www.vgm2020.com/static/nhl/nhl-test.json"

            continue

# taken from https://stackoverflow.com/questions/11122291/how-to-find-char-in-string-and-get-all-the-indexes
def find(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]

@client.event
async def on_message(message):
    send_to_discord = param_send_to_discord
    message_content = ""
    message_send = ""
    message_author = ""
    message_author_mention = ""
    message_channel_id = 0
    if isinstance(message,str):
        message_author = "CONSOLEUSER"
        message_content = message
        message_author_mention = "@" + message_author
        message_channel_id = 737889363119308932
    elif isinstance(message,discord.Message):
        message_content = message.content
        message_author = message.author
        message_author_mention = message.author.mention
        message_channel_id = message.channel.id

    echo_split = 2
    if "onlyconsole" in message_content:
        send_to_discord = False
        echo_split = 3

    if "channel=" in message_content:
        echo_split = echo_split + 1
        message_channel_id = message_content.split("=")[1].split(" ")[0]

#    message_content = " ".join(message_content.split(" ")[echo_split:]).lower() + " " + " ".join(message_content.split(" ")[:echo_split])
    " ".join(message_content.split(" ")[:echo_split]) + " " + " ".join(message_content.split(" ")[echo_split:])

    if "echo" in message_content:
        print("Echo command received")
        message_send = " ".join(message_content.split(" ")[echo_split:])
    elif "hello" in message_content:
        print("Hello command received")
        message_send = 'Hello ' + message_author_mention
    elif "help" in message_content:
        message_send = " ------ NHL GameCenter Bot Command List ------\n\n\"!nhl hello\"\tThe bot says hello to you! How nice of them!\n\"!nhl echo <insert message to repeat here>\"\tRepeats a message. Please use this for good!\n\"!nhl get scores\"\tRetrieves scores of all games currently being played.\n\"!nhl get schedule\"\tRetrieves start times of all scheduled games today as well as today's live scores\n\"!nhl get standings\"\tGets standings for entire league (NHL).\n\"!nhl get standings <insert either north, central, east, or west here>\"\tGets division standings for NHL North, Central, East, and West divisions."
    elif "get" in message_content:
        if echo_split > len(message_content.split(" ")):
            message_send = "Sorry, I don't know that command!"
        else:
            get_path = "get_" + message_content.split(" ")[echo_split] + ".py"

            if Path(get_path).is_file():
#               if exec_get is None:
                exec_get = importlib.import_module(get_path[:-3])
#                else:
#                    exec_get = importlib.reload(get_path[:-3])

                importlib.reload(exec_get)

                param = ""
                if len(message_content.split(" ")) > (echo_split + 1):
                    param = " ".join(message_content.split(" ")[(echo_split + 1):])
                    message_send = exec_get.exec_get_func(client = client, param = param)
                else:
                    message_send = exec_get.exec_get_func(client = client)
            else:
                message_send = "Sorry, I don't know that command!"

    else:
        message_send = "Sorry, I don't know that command!"
    
    # we do not want the bot to reply to itself
    if message_author == client.user:
        return

    if message_content.lower().startswith('!nhl') or  message_content.lower().startswith('!nwhl'):
        await nhlgb.send_discord_message(message_send, discord_client = client, channel_id = message_channel_id, console_mode = console_mode, send_to_discord = send_to_discord)

async def run_command(loop, arg, console=True):
    global console_mode
    old_console_mode = console_mode
    console_mode = console
    await on_message("!nhl " + arg)
    console_mode = old_console_mode
    

class SimpleCommander(Cmd):
    def __init__(self, mode, intro, prompt):
        # We need to pass in Cmd class mode of async cmd running
        super().__init__(mode=mode)
        self.intro = intro
        self.prompt = prompt
        self.loop = None

    def do_nhl(self, arg):
        try:
            self.loop.run_until_complete(run_command(self.loop, arg))
        except Exception as e:
            if str(e) == 'This event loop is already running':
                pass
        #await on_message("!nhl " + arg)

    def do_noconsole(self, arg):
        if "nhl" in arg:
            self.loop.run_until_complete(run_command(self.loop, " ".join(arg.split(" ")[1:]), console=False))
        else:
            print("noconsole: command unrecognized")

    def emptyline(self):
        pass

    def start(self, loop=None):
        # We pass our loop to Cmd class.
        # If None it try to get default asyncio loop.
        self.loop = loop
        # Create async tasks to run in loop. There is run_loop=false by default
        super().cmdloop(loop)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="\"!nhl help\" for help"))
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

async def console_shell():
    print("Starting console mode....")

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        mode = "Run"
    else:
        loop = asyncio.get_event_loop()
        mode = "Reader"
    # create instance
    cmd = SimpleCommander(mode=mode, intro="NHL Bot Console 1.0", prompt="(nhl-bot)> ")
    cmd.start(loop)  # prepaire instance
    try:
        loop.run_forever()  # our cmd will run automatilly from this moment
    except KeyboardInterrupt:
        loop.stop()

async def start_main_loop():
    await client.wait_until_ready()
    try:
        await asyncio.sleep(1)

        if console_mode:
            await console_shell()
                    
        #print("TOR " + str(active_games["TORatCBJ"]["TOR"]) + " CBJ " + str(active_games["TORatCBJ"]["CBJ"]))
    except Exception as e:
        if not str(e) == 'This event loop is already running':
            print(str(e), file=sys.stderr)
        pass

def main():
    print("NHL GameBreak Bot AI Server v1.0. Initializing....")
    print("Datasource URL: " + games_url)

    if param_send_to_discord:
        print("Send to Discord mode: Enabled")
    else:
        print("Send to Discord mode: Disabled")

    if console_mode:
        print("Console mode: Enabled")
    else:
        print("Console mode: Disabled")

    client.loop.create_task(start_main_loop())
    client.run(nhlgb.get_settings()["token"])

main()
