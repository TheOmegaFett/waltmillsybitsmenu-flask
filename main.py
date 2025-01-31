import asyncio
import twitchio
from twitchio.ext import commands
import random

class Bot(commands.Bot):
    def __init__(self):
        # Your existing bot initialization code here
        self.protected_users = set()  # Set to track protected users
        self.dropbear_active = False  # Flag for active drop bear event
        
    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        
    @commands.command(name='protect')
    async def protect_command(self, ctx):
        if self.dropbear_active:
            self.protected_users.add(ctx.author.name)
            await ctx.send(f'Fair dinkum! {ctx.author.name} survived the Drop Bear attack!')
            
    @commands.command(name='dropbear')  # Command to trigger drop bear event
    async def dropbear_command(self, ctx):
        if not self.dropbear_active:  # Only start if no active event
            self.protected_users.clear()  # Clear previous protections
            self.dropbear_active = True
            
            locations = ['cricket pitch', 'footy oval', 'bush track', 'billabong']
            items = ['Fairy bread force field', 'Golden Gaytime staff', 'Vegemite shield']
            
            location = random.choice(locations)
            item = random.choice(items)
            
            await ctx.send(f'🐨 STREWTH! Drop Bear spotted near the {location}! Quick, type !protect to use your {item}!')
            
            # Schedule end of drop bear event
            await asyncio.sleep(30)
            self.dropbear_active = False
            self.protected_users.clear()

bot = Bot()
bot.run()
