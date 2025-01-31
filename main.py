import asyncio
import twitchio
from twitchio.ext import commands
import random

class Bot(commands.Bot):
    def __init__(self):
        # Your existing bot initialization code here
        self.protected_users = set()
        self.dropbear_active = False
        
    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        
    @commands.command(name='protect')
    async def protect_command(self, ctx):
        if self.dropbear_active:
            self.protected_users.add(ctx.author.name)
            await ctx.send(f'Fair dinkum! {ctx.author.name} survived the Drop Bear attack!')
            
    @commands.command(name='dropbear')
    async def dropbear_command(self, ctx):
        if not self.dropbear_active:
            # Clear at start
            self.protected_users.clear()
            self.dropbear_active = True
            
            locations = ['cricket pitch', 'footy oval', 'bush track', 'billabong', 'Centrelink queue', 'gum tree']
            items = ['Fairy bread force field', 'Golden Gaytime staff', 'Vegemite shield', 'VB chain mail']
            
            location = random.choice(locations)
            item = random.choice(items)
            
            await ctx.send(f'🐨 STREWTH! Drop Bear spotted near the {location}! Quick, type !protect to use your {item}!')
            
            # Create separate task for ending the event
            asyncio.create_task(self.end_dropbear_event())
    
    async def end_dropbear_event(self):
        await asyncio.sleep(30)
        self.dropbear_active = False
        self.protected_users.clear()  # Clear at end

bot = Bot()
bot.run()
