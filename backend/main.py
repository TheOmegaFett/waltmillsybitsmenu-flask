import asyncio
import re
import redis
from twitchio.ext import commands, pubsub
from twitchio.ext.pubsub import PubSubPool
import os
import dotenv
import json
from datetime import datetime, date, timedelta
import logging
import websockets

dotenv.load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Bot(commands.Bot):
    """
    A Twitch bot that handles chat commands and events.
    Inherits from TwitchIO's commands.Bot class.
    """
    def __init__(self):
        super().__init__(
            token=os.getenv('BOT_TOKEN'),
            client_id=os.getenv('CLIENT_ID'),
            nick=os.getenv('BOT_USERNAME'),
            prefix='!',
            initial_channels=[os.getenv('TWITCH_CHANNEL')]
        )
        self.viewer_data = self.load_viewer_data()
        self._pubsub = PubSubPool(self)
        logger.info("Bot initialized with PubSub pool")

    async def setup_redis_listener(self):
        self.redis_task = asyncio.create_task(self._listen_to_redis())

    async def _listen_to_redis(self):
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        pubsub = redis_client.pubsub()
        pubsub.subscribe('bot_commands')
    
        while True:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                if data['type'] == '!dropbear':
                    # Create a mock context for the dropbear command
                    channel = self.get_channel(os.getenv('TWITCH_CHANNEL'))
                    mock_ctx = type('Context', (), {'send': channel.send, 'author': type('Author', (), {'is_mod': True, 'is_broadcaster': True})()})()
                    await self.dropbear(mock_ctx)
            await asyncio.sleep(0.1)

    def load_viewer_data(self):
        try:
            with open('viewer_data.json', 'r') as f:
                data = f.read()
                return json.loads(data) if data else {}
        except FileNotFoundError:
            # Create a new file with an empty JSON object
            with open('viewer_data.json', 'w') as f:
                json.dump({}, f)
                return {}

    async def event_ready(self):
        logger.info(f'Logged in as | {self.nick}')
        logger.info(f'Connected to channel | {os.getenv("TWITCH_CHANNEL")}')
    
        channel = self.get_channel(os.getenv('TWITCH_CHANNEL'))
        await channel.send("G'day legends! 🦘 Your friendly neighborhood bot is here, ready to throw some shrimps on the barbie and watch out for drop bears! Let's have a ripper of a stream!")

        try:
            topics = [
                pubsub.channel_points(os.getenv('TWITCH_TOKEN'))[os.getenv('CHANNEL_ID')]
            ]
            await self._pubsub.subscribe_topics(topics)
            logger.info("Successfully subscribed to channel points")
        except Exception as e:
            logger.error(f"PubSub connection failed: {str(e)}", exc_info=True)            
            return {}

        # Add Redis listener setup
        await self.setup_redis_listener()    

    def save_viewer_data(self):
        with open('viewer_data.json', 'w') as f:
            json.dump(self.viewer_data, f)

    def get_user_stats(self, username):
        """Get or create user stats"""
        if 'aussie_ranks' not in self.viewer_data:
            self.viewer_data['aussie_ranks'] = {}
        
        if username not in self.viewer_data['aussie_ranks']:
            self.viewer_data['aussie_ranks'][username] = {
                "rank": "Fresh Off The Boat",
                "points": 0,
                "drop_bear_survivals": 0,
                "vegemite_level": 0,
                "achievements": []
            }
        return self.viewer_data['aussie_ranks'][username]

    def add_points(self, username, points):
        """Add points to user"""
        stats = self.get_user_stats(username)
        stats["points"] += points
        self.update_rank(username)
        self.save_viewer_data()
        return stats["points"]

    def remove_points(self, username, points):
        """Remove points from user"""
        stats = self.get_user_stats(username)
        stats["points"] = max(0, stats["points"] - points)  # Prevent negative points
        self.update_rank(username)
        self.save_viewer_data()
        return stats["points"]

    def update_rank(self, username):
        """Update user rank based on points"""
        stats = self.get_user_stats(username)
        if stats["points"] >= 1000:
            stats["rank"] = "True Blue Legend"
        elif stats["points"] >= 500:
            stats["rank"] = "Fair Dinkum Mate"
        elif stats["points"] >= 100:
            stats["rank"] = "Proper Aussie"
        else:
            stats["rank"] = "Fresh Off The Boat"

    def get_points(self, username):
        """Get current points for user"""
        stats = self.get_user_stats(username)
        return stats["points"]


    async def event_message(self, message):
        """
        Event handler that triggers on every chat message.

        Args:
            message: The message object containing sender and content information
        """

        # Ignore messages sent by the bot itself
        if message.echo:
            return
    
        content = message.content.lower()
    
        # Track viewer activity
        viewer_name = message.author.name
        today = date.today().isoformat()
    
        if viewer_name not in self.viewer_data:
            self.viewer_data[viewer_name] = {
                "last_seen": today,
                "streak": 1,
                "total_visits": 1,
                "dates": [today]
            }
        else:
            viewer_data = self.viewer_data[viewer_name]
            if today not in viewer_data["dates"]:
                viewer_data["dates"].append(today)
                if viewer_data["last_seen"] == (date.today() - timedelta(days=1)).isoformat():
                    viewer_data["streak"] += 1
                else:
                    viewer_data["streak"] = 1
                viewer_data["total_visits"] += 1
                viewer_data["last_seen"] = today
    
        self.save_viewer_data()
    
        # Raid notifications
        if "just raided the channel with" in content:
            parts = message.content.split()
            raider = parts[0]
            count = parts[6]
            await message.channel.send(f"Welcome raiders! Thank you {raider} for bringing {count} awesome people!")
            await message.channel.send(f"!so {raider}")
    
        # New subscriber
        if "just subscribed" in content:
            parts = message.content.split()
            username = parts[0]
            await message.channel.send(f"Welcome to the Walt Show {username}! Thank you for supporting the channel!")
    
        # Gifted subs
        if "gifted" in content and "subscription" in content:
            await message.channel.send(f"Thank you for gifting {message.author.name}!")
    
        # Bits cheered
        # Look for cheer pattern (word 'cheer' followed by number)
        cheer_match = re.search(r'cheer(\d+)', content)
        if cheer_match:
            cheer_amount = int(cheer_match.group(1))
            if cheer_amount >= 100:
                await message.channel.send(f"Amazing! Thank you {message.author.name} for the massive {cheer_amount} bit cheer!")
            elif cheer_amount >= 50:
                await message.channel.send(f"Wow! Thanks for the bitties {message.author.name}!")
            elif cheer_amount >= 0:
                await message.channel.send(f"Thanks for the bits {message.author.name}!")
            
        # Follow alerts
        if "followed the channel" in content:
            await message.channel.send(f"Thanks for the follow! We appreciate you {message.author.name}!")
        
        # Host notifications
        if "now hosting" in content:
            await message.channel.send(f"Thanks for the host!")
        
        # Log all chat messages to console
        print(f"{message.author.name}: {message.content}")
        # Process any commands in the message
        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx):
        """
        Command handler for !hello command.
        Responds with a greeting to the user who triggered it.

        Args:
            ctx: The context object containing information about the command invocation
        """
        await ctx.send(f'Hello {ctx.author.name}!')

    @commands.command()
    async def streak(self, ctx):
        """Shows the viewer's current watch streak"""
        viewer = ctx.author.name
        if viewer in self.viewer_data:
            data = self.viewer_data[viewer]
            await ctx.send(f"{viewer} has a {data['streak']} day streak! Total visits: {data['total_visits']}")
        else:
            await ctx.send(f"Welcome to your streaks first stream, {viewer}!")
        
    @commands.command()
    async def dropbear(self, ctx):
        """
        Triggers a random Drop Bear event in chat. Moderator only command.
        """
        # Check if user is moderator or broadcaster
        if not ctx.author.is_mod and not ctx.author.is_broadcaster:
            await ctx.send(f"Oi mate {ctx.author.name}, only the Drop Bear experts (mods) can trigger these deadly creatures!")
            return

        # Check if there's already an active drop bear event
        if getattr(self, 'drop_bear_active', False):
            await ctx.send("Strewth! There's already a drop bear on the loose!")
            return

        import random

        aussie_items = [
            "Vegemite shield", 
            "thong armor", 
            "cork hat", 
            "Tim Tam sword",
            "Bunnings sausage shield",
            "Akubra helmet",
            "VB chain mail",
            "Lamington armor",
            "Meat pie throwing stars",
            "Fairy bread force field",
            "Golden Gaytime staff",
            "Milo energy shield",
            "Weet-Bix war hammer",
            "Paddle Pop sword"
        ]

        locations = [
            "gum tree",
            "Bunnings snag stand",
            "bottle-o",
            "servo",
            "local Maccas",
            "Woolies parking lot",
            "footy oval",
            "milk bar",
            "RSL",
            "local bowlo",
            "beach car park",
            "fish and chip shop",
            "cricket pitch",
            "local pub",
            "Centrelink queue",
            "train station pie warmer"
        ]

        # Set the drop bear status to active
        self.drop_bear_active = True
        print(f"Drop bear status: {self.drop_bear_active}")  # Log the status

        item = random.choice(aussie_items)
        location = random.choice(locations)

        await ctx.send(f"🐨 STREWTH! Drop Bear spotted near the {location}! Quick, type !protect to use your {item}!")

        # Give chat 15 seconds to protect themselves
        import asyncio
        await asyncio.sleep(15)

        # Check who survived
        survivors = getattr(self, 'protected_viewers', set())
        if survivors:
            await ctx.send(f"Fair dinkum! {', '.join(survivors)} survived the Drop Bear attack!")
        else:
            await ctx.send("Crikey! The Drop Bear got everyone!")

        # Reset for next drop bear attack
        self.drop_bear_active = False
        print(f"Drop bear status: {self.drop_bear_active}")  # Log the status
        self.protected_viewers = set()
    
    
    @commands.command()
    async def protect(self, ctx):
        """
        Lets viewers protect themselves from the Drop Bear
        """
        if getattr(self, 'drop_bear_active', False):
            self.protected_viewers = getattr(self, 'protected_viewers', set())
            self.protected_viewers.add(ctx.author.name)
            # Update their stats
            if 'aussie_ranks' in self.viewer_data:
                stats = self.viewer_data['aussie_ranks'].get(ctx.author.name, {
                    "rank": "Fresh Off The Boat",
                    "points": 0,
                    "drop_bear_survivals": 0,
                    "vegemite_level": 0,
                    "achievements": []
                })
            
                stats["drop_bear_survivals"] += 1
                stats["points"] += 5
            
                # Check for achievements
                if stats["drop_bear_survivals"] == 1:
                    stats["achievements"].append("Drop Bear Survivor")
                elif stats["drop_bear_survivals"] >= 10:
                    stats["achievements"].append("Drop Bear Whisperer")
                
                self.viewer_data['aussie_ranks'][ctx.author.name] = stats
                self.save_viewer_data()
        
            await ctx.send(f"{ctx.author.name} is safe as houses!")

    @commands.command()
    async def dice(self, ctx):
        """
        Rolls a dice for fun channel interactions
        """
     # Get everything after the command
        message = ctx.message.content.split(' ', 1)[1] if len(ctx.message.content.split(' ', 1)) > 1 else ''
        if message.lower() == '':
            await ctx.send('Please specify a bet for either high, low or 7. ie. !dice high')
            return
        import random
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)
        total = roll1 + roll2
        await ctx.send(f"{ctx.author.name} rolled a {roll1} and {roll2} for a total of {total}! 🎲")
        if message.lower() == 'high':
            if total > 7:
                await ctx.send(f"{ctx.author.name} wins! 🎉")
            else:
                await ctx.send(f"{ctx.author.name} loses! 💸")
        if message.lower() == 'low':
            if total < 7:
                await ctx.send(f"{ctx.author.name} wins! 🎉")
            else:
                await ctx.send(f"{ctx.author.name} loses! 💸")
        if message.lower() == '7':
                if total == 7:
                    await ctx.send(f"{ctx.author.name} wins! 🎉")
                else:
                    await ctx.send(f"{ctx.author.name} loses! 💸")

    @commands.command()
    async def weather(self, ctx):
        """
        Get the current weather for WaltMillsy's Studio in Sydney with Aussie flair
        """
        import requests

        # WeatherAPI.com endpoint for Sydney
        api_key = os.getenv('WEATHER_API_KEY')
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q=Sydney&aqi=no"

        try:
            response = requests.get(url)
            data = response.json()

            temp = data['current']['temp_c']
            humidity = data['current']['humidity']
            conditions = data['current']['condition']['text']

            # Aussie slang temperature descriptions
            temp_description = (
                "Bloody freezing | " if temp < 15 else
                "She's a bit nippy | " if temp < 20 else
                "Perfect for a barbie | " if temp < 25 else
                "Strewth it's hot | " if temp < 30 else
                "It's a scorcher | "
            )

            # Aussie slang weather conditions
            weather_slang = {
                "sunny": "clear as a bottla VB | ",
                "cloudy": "grey as a galah | ",
                "rain": "pissing down | ",
                "storm": "going off like a frog in a sock | ",
                "windy": "blowing like a dunny door in a hurricane | ",
                "overcast": "gloomy as a Bunnings without snags | ",
                "clear": "beautiful as | "
            }

            condition_key = next((k for k in weather_slang if k in conditions.lower()), "fair dinkum beautiful")

            await ctx.send(
                f"🦘 Bonza Weather Report from WaltMillsy's Studio 🦘\n"
                f"Temp: {temp}°C - {temp_description}\n"
                f"Weather's {weather_slang.get(condition_key, conditions)}\n"
                f"Humidity's sitting at {humidity}% - {'sticky as a meat pie' if humidity > 70 else 'dry as a dead dingo'}"
            )

        except Exception as e:
            await ctx.send("Crikey! The weather report's gone walkabout! Try again later, mate!")
    
        
    

    @commands.command()
    async def fair_dinkum(self, ctx):
        """
        Check your Aussie Rank and achievements
        """
        viewer = ctx.author.name
        
        if 'aussie_ranks' not in self.viewer_data:
            self.viewer_data['aussie_ranks'] = {}
            
        if viewer not in self.viewer_data['aussie_ranks']:
            self.viewer_data['aussie_ranks'][viewer] = {
                "rank": "Fresh Off The Boat",
                "points": 0,
                "drop_bear_survivals": 0,
                "vegemite_level": 0,
                "achievements": []
            }
        
        stats = self.viewer_data['aussie_ranks'][viewer]
        
        # Update rank based on points
        if stats["points"] >= 1000:
            stats["rank"] = "True Blue Legend"
        elif stats["points"] >= 500:
            stats["rank"] = "Fair Dinkum Mate"
        elif stats["points"] >= 100:
            stats["rank"] = "Proper Aussie"
        
        await ctx.send(f"🦘 {viewer}'s Aussie Stats 🦘\n"
                    f"Rank: {stats['rank']} | Drop Bear Survivals: {stats['drop_bear_survivals']} | Vegemite Level: {stats['vegemite_level']}/10 | Achievements: {', '.join(stats['achievements']) if stats['achievements'] else 'None yet, mate!'}")
        
        self.save_viewer_data()

    # @commands.command()
    # async def raid(self, ctx):
    #     """
    #     Command handler for !raid command.
    #     Responds with a raiding message to the channel. Only works for user WaltMillsy.
    #     Args:
    #         ctx: The context object containing information about the command invocation
    #     """
    #     if ctx.author.name.lower() == 'theomegafett':
    #         await ctx.send('WaltMillsy is raiding! Use msg WaltMiRAID2 waltmiRAID2 waltmiHYPE')
    #     else:
    #         print(f"Raid command denied for user: {ctx.author.name}")



async def listen_to_channel_points(bot):
    uri = "wss://pubsub-edge.twitch.tv"
    access_token = os.getenv('TWITCH_TOKEN').replace('oauth:', '')
    await bot.wait_for_ready()
    channel = bot.get_channel(os.getenv('TWITCH_CHANNEL'))
    channel_id = os.getenv('CHANNEL_ID')

    while True:  # Outer loop for reconnection
        try:
            async with websockets.connect(uri) as websocket:
                # Initial LISTEN message
                message = {
                    "type": "LISTEN",
                    "data": {
                        "topics": [f"channel-points-channel-v1.{channel_id}"],
                        "auth_token": access_token
                    }
                }
                await websocket.send(json.dumps(message))
                
                # Keep-alive ping task
                async def send_ping():
                    while True:
                        ping_message = {"type": "PING"}
                        await websocket.send(json.dumps(ping_message))
                        await asyncio.sleep(240)  # Send ping every 4 minutes
                
                # Start ping task
                ping_task = asyncio.create_task(send_ping())
                
                # Main message handling loop
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if data['type'] == 'PONG':
                        logger.info("Received PONG from server")
                        continue
                        
                    if data['type'] == 'MESSAGE':
                        message_data = json.loads(data['data']['message'])
                        if message_data['type'] == 'reward-redeemed':
                            redemption = message_data['data']['redemption']
                            user = redemption['user']['display_name']
                            reward = redemption['reward']
                            title = reward['title']
                            cost = reward['cost']
                            logger.info(f"{user} redeemed {title}! for {cost} points!")
                            await channel.send(f"{user} redeemed {title}! for {cost} points!")
                            
                            # Handle specific rewards
                            if title == 'yipi!!!!!':
                                await channel.send("yipi!!!!!")
                            elif title == '1ST':
                                await channel.send(f"Congratulations {user}! You are the 1ST reward redeemer! +50 Points!")
                                bot.add_points(user, 50)
                            elif title == '2ND':
                                await channel.send(f"Congratulations {user}! You are the 2ND reward redeemer! +20 Points!")
                                bot.add_points(user, 20)
                            elif title == '3RD':
                                await channel.send(f"Congratulations {user}! You are the 3RD reward redeemer! +5 Points!")
                                bot.add_points(user, 5)

        except websockets.exceptions.ConnectionClosedError:
            logger.warning("WebSocket connection closed. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await asyncio.sleep(5)
        finally:
            if 'ping_task' in locals():
                ping_task.cancel()


async def start_bot():
    bot = Bot()
    print("Bot initialized")
    
    # Create tasks for both the bot and channel points listener
    bot_task = bot.start()
    points_task = listen_to_channel_points(bot)  # Pass bot instance
    
    # Run both tasks concurrently
    await asyncio.gather(bot_task, points_task)
    
    

