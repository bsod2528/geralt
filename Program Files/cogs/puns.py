import asyncio
from os import name
import discord
import json
import random
import datetime
from discord import reaction
from discord import mentions
import asyncpg
from discord.colour import Color
from discord.ext import commands

class Puns(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.from_rgb(117, 128, 219)
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.json = json.load(open('Emotes.json'))   

    @commands.command(
        aliases   =   ['fb', 'friendsb'], 
        help = '```ini\n[ Syntax : .gfriendsburn <user> ]\n```\n>>> **USE : **Roast your friends with amazing insults.\n**AKA :** `.gfb` `.gfriendsb`')
    async def friendsburn(self, ctx, member: discord.Member):
        roast = ['You are more disappointing than an unsalted pretzel.',
                'You have so many gaps in your teeth it looks like your tongue is in jail.',
                'I could eat a bowl of alphabet soup and poop out a better name for myself than yours.',
                'From the bottom of my heart (with immense emphasis on From) --> YOU SUCK!',
                'Why dont you go check on eBay, to see whether they still sell a life.',
                'Youre the only reason why the gene pool needs a lifeguard.',
                'Its pointless to make fun of you, because youll spend the rest of the day to figure it out.',
                'Trash gets cleared at 8 AM every morning, be ready.',
                'You sound better with ya mouth closed.',
                'Id rather not roast you. Im using up unnecessary data by that.',
                'If I search loser in Google, the first thing pops up is your name.',
                'Why though? Do you think theres a use in roasting you?',
                'The people who tolerate you on a daily basis are the real heros of life.',
                'You’re like the end pieces of a loaf of bread. Everyone touches you, but nobody wants you.',
                'Your face makes onions cry.',
                'You’re not stupid! You just suck at thinking.',
                'Somewhere out there, there’s a tree working very hard to produce oxygen so that you can breathe. I think you should go and apologize to it.',
                'Calling you an idiot would be an insult to all stupid people.',
                'May both sides of your pillow be uncomfortably warm.',
                'You are like a cloud. When you disappear it’s a beautiful day.',
                'I was hoping for a battle of wits but you appear to be unarmed.',
                'Earth is full. Go home.',
                'Keep rolling your eyes, you might eventually find a brain.',
                'Your only purpose in life is to become an organ donor.',
                'You are proof that evolution can go in reverse.',
                'Unless your name is Google, stop acting like you know everything!',
                'I envy people who have never met you.',
                'Your so annoying that you made a Happy Meal cry.',
                'I’ll never forget the first time we met. But I’ll keep trying.',
                'You bring everyone so much joy when you leave the room.',
                'OH MY GOD! IT SPEAKS!',
                'Complete this sentence for me: “I never want to see you ____!”',
                'When you look in the mirror, say hi to the clown you see in there for me, would ya?',
                'Beauty is only skin deep, but ugly goes clean to the bone and your an example.',
                'Well, the jerk store called. They’re running out of you.',
                'Mirrors cant talk. Lucky for you they cant laugh either']
        emote = self.json
        delta   =   [f'{emote["panda"]["lesgo"]}',
                    f'{emote["peep"]["yeaboi"]}',
                    f'{emote["random_themed"]["salute"]}',
                    f'{emote["sed"]["whyme"]}',
                    f'{emote["linus"]["focboi"]}',
                    f'{emote["peep"]["space"]}',
                    f'{emote["random_themed"]["kek"]}',
                    f'{emote["linus"]["oo"]}',
                    f'{emote["random_themed"]["trumpclap"]}',
                    f'{emote["panda"]["cool"]}',
                    f'{emote["frog"]["hmm"]}',
                    f'{emote["anxiety"]["triggered"]}',
                    f'{emote["sed"]["sd"]}']
        emb = discord.Embed(
                title = '**Roast Your Friends**',
                description = f'{member.mention} {random.choice(roast)} {random.choice(delta)} ',
                color = self.color)
        emb.timestamp = self.timestamp
        await ctx.send(embed = emb)
    
    @commands.command(
        name = 'techburn', 
        aliases = ['tb', 'techb'], 
        help = f'```ini\n[ Syntax : .gtechburn <user> ]\n```\n>>> **USE :** En number of technical insults to roast your friends with.\n**AKA :** `.gtb` `.gtechb`')
    async def techburn(self, ctx, member : discord.Member):
        techroast = ['My CPU cores are faster than your brain registering what I just said',
                     'Honestly, DDR1 is better than you! Go suck on that punk.',
                     'Your slower than a 7200RPM HDD!',
                     'I have an update pending, I’d rather not talk you right now.',
                     'You vs a Pentium would be the best race in the world.',
                     'NVME, more like --> No Venting More Ellowed!',
                     'No matter how much RAM you have, you can never store more than 1 KB of data which your brain can’t even register.',
                     'You dont need an ATX case to fit your brain, all you need is a size smaller than the Vent of an old Laptop.',
                     'Why do you need a Thunderbolt 4 port, when all you need is a UBS 2.',
                     'The bitrate of your movement is slower than VGA’s.',
                     'Even a CS GO bot has better latency than your response.',
                     'You think so badly that even a game bot has better aim at its target than what you’re thinking at.',
                     '01111001 01101111 01110101 00100000 01101000 01100001 01110110 01100101 00100000 01101110 01101111 00100000 01101100 01101001 01100110 01100101 00001010',
                     'You really need to improve your BRAIN architecture, cos its slower than the 1st ever CPU to be ever made.',
                     'Your like Bulldozer architecture from AMD, looks good on the outside. But we all knew it sucked on the inside, your just like that.']
        emote = self.json
        epsilon =   [f'{emote["panda"]["lesgo"]}',
                    f'{emote["peep"]["yeaboi"]}',
                    f'{emote["random_themed"]["salute"]}',
                    f'{emote["sed"]["whyme"]}',
                    f'{emote["linus"]["focboi"]}',
                    f'{emote["peep"]["space"]}',
                    f'{emote["random_themed"]["kek"]}',
                    f'{emote["linus"]["oo"]}',
                    f'{emote["random_themed"]["trumpclap"]}',
                    f'{emote["panda"]["cool"]}',
                    f'{emote["frog"]["hmm"]}',
                    f'{emote["anxiety"]["triggered"]}',
                    f'{emote["sed"]["sd"]}']
        async with ctx.typing():
            emb = discord.Embed(
                title = '**Roast Your Friends, but Technically**',
                description = f'{member.mention} {random.choice(techroast)} {random.choice(epsilon)}', 
                color = self.color)
            emb.timestamp = self.timestamp
        await asyncio.sleep(0.5)    
        send = await ctx.send(embed = emb)
        await send.add_reaction('🔥')

    @commands.command(
        aliases = ['dj', 'dad'], 
        help = f'```ini\n[ Syntax : .gdadjoke ]\n```\n>>> **USE :** Spice up your day with DADJOKES!\n**AKA :** `.gdj` `dad`')
    async def dadjoke(self,ctx):
        jokes = ['To whoever stole my copy of Microsoft Office, I will find you.You have my Word!',
                 'Q: Why did the coffee file a police report? A: It got mugged.',
                 'Opener: A man says to a werewolf, “You’re a werewolf.” Punchline: The werewolf says, “I’m awere.”',
                 'My wife is so negative. I remembered the car seat, the stroller, AND the diaper bag. Yet all she can talk about is how I forgot the baby.',
                 'Q: Dad, did you get a haircut? A: No, I got them all cut.',
                 'Opener: My aunt’s astrological sign was cancer, funny to consider how she died. Punchline: She was killed by a giant crab.',
                 'Opener: Did you know that’s a popular cemetery? Punchline: People are just dying to get in there!',
                 'If a child refuses to sleep during nap time, are they guilty of resisting a rest?',
                 'Q: What’s faster, hot or cold? A: Hot, because you can catch a cold!',
                 'Q: What time did the man go to the dentist? A: Tooth hurt-y.',
                 'Opener: I recently bumped into the guy that sold me an antique globe. Punchline: It’s a small world.',
                 'Q: Dad, can you put my shoes on? A: No, I don’t think they’ll fit me.',
                 'Opener: My wife and I have decided not to have kids. Punchline: The kids are taking it pretty badly.',
                 'If you see a robbery at an Apple Store does that make you an iWitness?',
                 'Q: What’s the difference between a poorly dressed man on a tricycle and a well-dressed man on a bicycle? A: Attire!',
                 'Q: Why don’t eggs tell jokes? A: They’d crack each other up.',
                 'I don’t trust stairs. They’re always up to something!',
                 'Q: Why can’t a leopard hide? A: Because he’s always spotted',
                 'Q: How many apples grow on a tree? A: All of them.',
                 'It’s important to keep some candy in your pocket at all times. It could be a lifesaver.',
                 'Q: Did you hear about the kidnapping at school? A: He woke up.',
                 'Opener: I dreamed about drowning in an ocean made out of orange soda last night. Punchline: It took me a while to work out it was just a Fanta sea.',
                 'Opener: At work, we have a printer we’ve nicknamed Bob Marley. Punchline: It’s always Jammin’.',
                 'Opener: I went to the store to pick up 8 cans of Sprite. Punchline:  But when I got home I realized I’d only picked 7up.',
                 'Opener: My daughter screeched, “Daaaad, you haven’t listened to one word I’ve said, have you!?” Punchline: What a strange way to start a conversation with me.',
                 'I couldn’t get a reservation at the library… They were fully booked.',
                 'Q: What do you call someone with no body and no nose? A: Nobody knows.',
                 'Opener: I just saw my wife walk by with her sexiest underwear on, which can only mean one thing. Punchline: It’s laundry day.',
                 'My wife: He’s always trying to jeopardize our relationship. Therapist: And how do you respond to that? Me: I’ll take “My wife is being a big baby” for $500, Alex.',
                 'Q: What is the least spoken language in the world? A: Sign language.',
                 'Opener: I bought some shoes from a drug dealer. Punchline: I don’t know what he laced them with, but I was tripping all day!',
                 'Q: How did the dog stop the music? A: Paws.',
                 'The problem with Nearly Headless Nick is that he’s a poorly executed character.',
                 'Opener: I accidentally got rice in my headphone jack. Punchline: Now all my music sounds grainy.',
                 'Opener: My wife tried to unlatch our daughter’s car seat with one hand and said, “How do one-armed mothers do it?” Punchline: Without missing a beat I replied, “Single handedly.”',
                 'Q: Why don’t skeletons ever go trick or treating? A: Because they have no body to go with.',
                 'Q: I just watched a documentary about beavers. A: It was the best dam show I ever saw!',
                 'Q: I ordered a chicken and an egg from Amazon. A: I’ll let you know.',
                 'Q: This graveyard looks overcrowded. A: People must be dying to get in there!',
                 'Reversing the car ‘Ahh, this takes me back.’',
                 'Q: What did the buffalo say when his son left? A: Bison!',
                 'Q: What do you call a dinosaur that is sleeping? A: A dino-snore!',
                 'Don’t trust atoms. They make up everything!',
                 'Q: Did you know that humans eat more bananas than monkeys? A: It’s true. I mean when was the last time you ate a monkey?',
                 'Q: What’s the funniest city in Louisiana? A:  Laugh-ayette.',
                 'Q: Why did the cookie go to the hospital? A: Because he felt crummy.',
                 'Well, we were having dinner, and Dad had spilled his peas on the table… He looks right at me and said, “Oh no, I have just peed on the table.”',
                 'Opener: I’m reading a book about anti-gravity. Punchline: It’s impossible to put down!',
                 'Opener: I thought about going on an all-almond diet…. Punchline: But that’s just nuts!',
                 'Q: What do you call a Mexican who has lost his car? A: Carlos.',
                 'Q: Is your refrigerator running? A: Because I might vote for it…',
                 'Chris Hemsworth is Australian and Thor is from space does that make him an Australien?',
                 'Opener: Spring is here! Punchline: I got so excited I wet my plants!',
                 'Q: Can February March? A: No, but April May!',
                 'Q: What did the drummer call his twin baby daughters? A: Anna1 Anna2',
                 'Q: What’s orange and sounds like a parrot. A: A carrot!',
                 'Opener: I never wanted to believe that my Dad was stealing from his job as a road worker. Punchline: But when I got home, all the signs were there.',
                 'Doctor: [handing me my newborn baby] I’m sorry but your wife didn’t make it Me: [handing baby back to him] bring me the one my wife made.',
                 'Q: You’re American when you go into the bathroom, and you’re American when you come out, but do you know what you are while you’re in there? A: European.',
                 'Q: Did you hear about the cheese factory that exploded in France? Answer: There was nothing left but de Brie.',
                 'Q: What’s brown and sticky? Answer: A stick.',
                 'Opener: The secret service isn’t allowed to yell “Get down!” anymore when the president is about to be attacked. Punchline: Now they have to yell “Donald, duck!”',
                 'Dad asks me, “Have you heard about the new movie constipation?” I was like, “What? No.” And he said, “It never came out.”',
                 'Opener: I am suspicious that my wife is secretly adding glue to my weapons collection. Punchline: She denies it, but I’m sticking to my guns.',
                 'Q: What do you call a hippie’s wife? A: Mississippi.',
                 'Is a rivalry between two vegetarians still called a beef?',
                 'Opener: I start a new job in Seoul next week. Punchline: I hope it is going to be a good Korea move.',
                 'Opener: Do I enjoy making courthouse puns? Punchline: Guilty.',
                 'Opener: I can’t decide if I want to pursue a career as a writer or a grifter. Punchline: I’m still weighing the prose and cons.',
                 'I don’t often tell dad jokes, but when I do, he laughs.',
                 'Q: Dad walks into a bookstore and says, “ Can I have a book by Shakespeare?” “Of course, sir, which one?” A: William.',
                 'Q: What’s better than Ted Danson? A: Ted singing and Danson!'
                 'Why don’t crabs give to charity? Because they’re shellfish.',
                 'Why did the man name his dogs Rolex and Timex? Because they were watch dogs.',
                 'What did the evil chicken lay? Deviled eggs.',
                 'What’s the best way to watch a fly-fishing tournament? Live stream.',
                 'My wife asked me to sync her phone, so I threw it into the ocean. I don’t know why she’s mad at me.',
                 'Why is grass so dangerous? Because it’s full of blades.',
                 'How do you tell the difference between an alligator and a crocodile? You will see one later and one in a while.',
                 'What do you call a dog that can do magic? A Labracabrador.',
                 'Why do you never see elephants hiding in trees? Because they’re so good at it.',
                 'What happens when it rains cats and dogs? You have to be careful not to step in a poodle.',
                 'What do you call 50 pigs and 50 deer? 100 sows and bucks.',
                 'Why do cows wear bells? Because their horns don’t work.',
                 'What do you call a fish with no eye? A fsh.',
                 'Police arrested a bottle of water because it was wanted in three different states: Solid, liquid, and gas.',
                 'What do you call a lazy kangaroo? Pouch potato.',
                 'I got hit in the head with a can of Diet Coke today. Don’t worry, I’m not hurt. It was a soft drink.',
                 'Why do melons have weddings? Because they cantaloupe.',
                 'What do you call a fake noodle? An impasta.',
                 'A ham sandwich walks into a bar and orders a beer. The bartender says, “Sorry, we don’t serve food here.”',
                 'Cooking out this weekend? Don’t forget the pickle. It’s kind of a big dill.',
                 'A cheese factory exploded in France. Da brie is everywhere!',
                 'Justice is a dish best served cold. If it were served warm, it would be justwater.',
                 'What’s orange and sounds like a parrot? A carrot.',
                 'Did you hear the rumor about butter? Well, I’m not going to spread it!',
                 'A steak pun is a rare medium done well.',
                 'In a freak accident today, a photographer was killed when a huge lump of cheddar landed on him. To be fair, the people who were being photographed did try to warn him.',
                 'Why did the raisin go out with the prune? Because he couldn’t find a date.',
                 'I want to go on record that I support farming. As a matter of fact, you could call me protractor.',
                 'Can February March? No, but April May.']
        emote = self.json
        zeta    =   [f'{emote["panda"]["aww"]}',
                    f'{emote["panda"]["lesgo"]}',
                    f'{emote["panda"]["blob"]}',
                    f'{emote["panda"]["clap"]}',
                    f'{emote["panda"]["slide"]}',
                    f'{emote["panda"]["awwshake"]}',
                    f'{emote["panda"]["duckdance"]}',
                    f'{emote["panda"]["cool"]}']
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = 'Dad Jokes! He He',
            description = f'{random.choice(jokes)} {random.choice(zeta)}',
            color = self.color)
        emb.timestamp = self.timestamp
        send = await ctx.reply(embed = emb)
        await send.add_reaction('🤌')

def setup(bot):
    bot.add_cog(Puns(bot))