'''
Package imports
'''
import discord, asyncio, datetime
from discord.ext import commands, tasks
from getRawData import *

'''
Constants and bot initilization.
'''
with open('bot.token', 'r') as tokenFile:
    TOKEN = tokenFile.read().strip()
tokenFile.close()

USER_ID_LENGTH = 18
DAILY_CASE_LOCATION = 3
TOTAL_CASE_LOCATION = 7
SCHOOL_BANNER_LINK = "https://git.io/JUfcf"
description = '''A bot to streamline the COVID-19 stats from the BU testing dashboard'''
bot = commands.Bot(command_prefix='?', description=description)
registeredUsers = []

'''
Gather initial testing data.
First check is a bit complex in programming,
the driver gets created and then deleted to optimize somewhat,
data will then be updated from other functions.
'''
data = processData(getRawData(getDriver()))
latestDataDate = data[0]
lastChecked = datetime.datetime.now()

'''
Update the values in the background.
'''
def updateValues():
    # Probably not a great idea but it works.
    global data
    global latestDataDate
    global lastChecked

    # Driver and raw data
    driver = getDriver()
    rawData = getRawData(driver)

    # Important data to keep track of.
    data = processData(rawData)
    latestDataDate = data[0]
    lastChecked = datetime.datetime.now()

'''
Display bot information in the backend.
After bot boots up, loads in the users that want updates.
'''
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(discord.__version__)
    print('------')

    # Check how many servers this bot is serving.
    serverCount = 0
    for _ in bot.guilds:
        serverCount += 1
    print('Current server count: ' + str(serverCount))

    # Attempt to load in users that have already subscribed.
    try:
        with open('users', 'r') as users:
            for user in users:
                if len(user) == USER_ID_LENGTH + 1:
                    registeredUsers.append(bot.get_user(int(user[0:USER_ID_LENGTH])))
    except:
        # users file not found / insufficient permissions to read.
        print("No subscriber list found")

'''
Background task to call update every 10 minutes.
If a new case has been detected, the bot will privately message all
users who are signed up for updates through the register command.
'''
@tasks.loop(minutes=10.0)
async def updateDashboard():
    print("Updating stats...")
    # tempDate use to compare and check if the data is new or just the same day.
    tempDate = latestDataDate
    updateValues()
    # Report data array to the backend, consult processData() for value meaning.
    print("Update finished on: " + lastChecked.strftime("%Y-%m-%d %H:%M:%S"))
    backendReport(data)

    # Check to see if the bot needs to send out alerts
    if data[DAILY_CASE_LOCATION] != 0 and data[0] != tempDate:
        print("New case detected, alerting users.")
        for user in registeredUsers:
            # Account for cases where an user account is deleted/banned
            if (user != None):
                try:
                    await user.send("Infections increased by %s on %s to a total of %s cases." %\
                        (data[DAILY_CASE_LOCATION], latestDataDate, data[TOTAL_CASE_LOCATION]))
                except:
                    print(str(user) + " does not allow private messages.")
    else:
        print("No new cases / No new data, no need to alert.")

'''
Helper for the background task, waits for the bot to be
ready before starting the tasks.
'''
@updateDashboard.before_loop
async def beforeReady():
    await bot.wait_until_ready()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="BU COVID-19 Statistics"))

'''
Bot command stats will return the testing information.
'''
@bot.command()
async def stats(ctx):
    """Returns status of BU's testing data."""

    # Construct the embed containing appropriate values.
    embed=discord.Embed(title="BU COVID-19 Testing Status", url="https://www.bu.edu/healthway/community-dashboard/", \
        description="📅 Latest avaliable data: " + data[0], color=0xcc0000)
    embed.set_thumbnail(url=SCHOOL_BANNER_LINK)
    embed.add_field(name=":microscope: Daily Tested:", value=data[1], inline=False)
    embed.add_field(name=":white_check_mark: Daily Negative:", value=data[2], inline=True)
    embed.add_field(name=":x: Daily Positive:", value=data[3], inline=True)
    embed.add_field(name=":microscope: Total Tested:", value=data[5], inline=False)
    embed.add_field(name=":white_check_mark: Total Negative:", value=data[6], inline=True)
    embed.add_field(name=":x: Total Positive:", value=data[7], inline=True)
    embed.add_field(name=":zipper_mouth: Isolation:", value=data[9], inline=False)
    embed.add_field(name=":innocent: Recovered:", value=data[10], inline=False)
    embed.set_footer(text="Last updated: " + lastChecked.strftime("%Y-%m-%d %H:%M:%S"))
    return await ctx.send(embed=embed)

'''
Registers a user to recieve updates on new case if one is detected.
Unregisteres a user if the register command is called when someone
is arleady registered.
Subscribers are stored as user id's, upon the bot restart it will
attempt to relocate the users via looking them up by id.
'''
@bot.command()
async def register(ctx):
    """Registeres/Removes an user to recieve notifications if someone is tested positive."""
    user = ctx.author
    # We need to add this user to the subscriber list.
    if user not in registeredUsers:
        registeredUsers.append(user)
        # This appraoch isn't efficient, but it works and I am not expecting too many users.
        with open('users', 'w') as userlist:
            for userEntry in registeredUsers:
                userlist.write('%s\n' % userEntry.id)
        userlist.close()
        return await ctx.send("<@%s>, you are registered to recieve updates"\
            % (str(user.id)))
    # This user wants to be removed from the subscriber list.
    else:
        registeredUsers.remove(user)
        with open('users', 'w') as userlist:
            for userEntry in registeredUsers:
                userlist.write('%s\n' % userEntry.id)
        userlist.close()
        return await ctx.send("<@%s>, you have been removed from receiving updates"\
            % (str(user.id)))

'''
Start background task and start bot.
'''
updateDashboard.start()
bot.run(TOKEN)
