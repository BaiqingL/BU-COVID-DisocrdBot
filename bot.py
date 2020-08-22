# Import web driver code.
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Constants.
ESTIMATED_DATA_LENGTH = 1300

'''
Initiate a driver instance of the chrome web browser to render the javascript.
'''
def getDriver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)
    return driver

'''
Since BU uses Microsoft Power BI to display data, it is a javascript driven page.
This means we need to use selenium to properly render and grab data.
'''
def getRawData(driver):
    driver.get('https://app.powerbi.com/view?r=eyJrIjoiMzI4OTBlMzgtODg5MC00OGEwLThlMDItNGJiNDdjMDU5ODhkIiwidCI6ImQ1N2QzMmNjLWMxMjEtNDg4Zi1iMDdiLWRmZTcwNTY4MGM3MSIsImMiOjN9')
    # We are looking for reportLandingContainer.
    rawDataSegment = ""
    while len(rawDataSegment) < ESTIMATED_DATA_LENGTH:
        rawDataSegment = driver.find_element_by_id('reportLandingContainer').text
    driver.quit()
    return rawDataSegment

'''
String manipulation to parse data.
'''
def processData(rawDataSegment):
    # Find date of the latest data.
    dateEndIndex = rawDataSegment.find("Positive")
    dateBeginIndex = rawDataSegment.rfind('\n',0,dateEndIndex-1)
    date = rawDataSegment[dateBeginIndex+1:dateEndIndex-1]

    # Find how many tests were done in a day.
    dailyTestEndIndex = rawDataSegment.find("Test Results")
    dailyTestBeginIndex = rawDataSegment.rfind('\n',0,dailyTestEndIndex-1)
    dailyTestConducted = rawDataSegment[dailyTestBeginIndex+1:dailyTestEndIndex-1]

    # Find how many tests were negative in day.
    dailyNegativeEndIndex = rawDataSegment.find("Negative Tests")
    dailyNegativeBeginIndex = rawDataSegment.rfind('\n',0,dailyNegativeEndIndex-1)
    dailyNegativeOutcome = rawDataSegment[dailyNegativeBeginIndex+1:dailyNegativeEndIndex-1]

    # Find how many tests were positive in a day.
    dailyPositiveEndIndex = rawDataSegment.find("Positive Tests")
    dailyPositiveBeginIndex = rawDataSegment.rfind('\n',0,dailyPositiveEndIndex-1)
    dailyPositiveOutcome = rawDataSegment[dailyPositiveBeginIndex+1:dailyPositiveEndIndex-1]

    # Find how many test were inconclusive.
    dailyInconclusiveOutcome = str(int(dailyTestConducted.replace(',','')) - int(dailyNegativeOutcome.replace(',','')) - int(dailyPositiveOutcome.replace(',','')))

    # Find how many tests were done in total.
    totalTestEndIndex = rawDataSegment.find("Test Results", dailyTestEndIndex+1)
    totalTestBeginIndex = rawDataSegment.rfind('\n',0,totalTestEndIndex-1)
    totalTestConducted = rawDataSegment[totalTestBeginIndex+1:totalTestEndIndex-1]

    # Find how many tests were negative in total.
    totalNegativeEndIndex = rawDataSegment.find("Negative Tests", dailyNegativeEndIndex+1)
    totalNegativeBeginIndex = rawDataSegment.rfind('\n',0,totalNegativeEndIndex-1)
    totalNegativeOutcome = rawDataSegment[totalNegativeBeginIndex+1:totalNegativeEndIndex-1]

    # Find how many tests were positive in total.
    totalPositiveEndIndex = rawDataSegment.find("Positive Tests", dailyPositiveEndIndex+1)
    totalPositiveBeginIndex = rawDataSegment.rfind('\n',0,totalPositiveEndIndex-1)
    totalPositiveOutcome = rawDataSegment[totalPositiveBeginIndex+1:totalPositiveEndIndex-1]

    # Find how many test were inconclusive.
    totalInconclusiveOutcome = str(int(totalTestConducted.replace(',','')) - int(totalNegativeOutcome.replace(',','')) - int(totalPositiveOutcome.replace(',','')))

    # Find how many students are in isolation.
    isolationCountEndIndex = rawDataSegment.find("Currently in Isolation")
    isolationCountBeginIndex = rawDataSegment.rfind('\n',0,isolationCountEndIndex-1)
    isolationCount = rawDataSegment[isolationCountBeginIndex+1:isolationCountEndIndex-1]

    # Data array constructed with below values.
    return [
        date,
        dailyTestConducted,
        dailyNegativeOutcome,
        dailyPositiveOutcome,
        dailyInconclusiveOutcome,
        totalTestConducted,
        totalNegativeOutcome,
        totalPositiveOutcome,
        totalInconclusiveOutcome,
        isolationCount
        ]
    
'''
Make the data look nicer in the backend.
'''
def backendReport(data):
    print("📅 Latest Date: " + data[0])
    print("\n")
    print("🔬 Daily: " + data[1])
    print("✔️ Daily Negative: " + data[2])
    print("🤒 Daily Positive: " + data[3])
    print("🤔 Daily Inconclusive: " + data[4])
    print("\n")
    print("🔬 Total: " + data[5])
    print("✔️ Total Negative: " + data[6])
    print("🤒 Total Positive: " + data[7])
    print("🤔 Total Inconclusive: " + data[8])
    print("\n")
    print("🥺 Isolation Count: " + data[9])


'''
Data extraction part complete, discord part below.
Example code skeleton structure from: https://github.com/Rapptz/discord.py/blob/master/examples/basic_bot.py
'''

'''
Discord related imports.
'''
import discord, asyncio, datetime
from discord.ext import commands, tasks

'''
Constants and bot initilization.
'''
TOKEN = 'bot token redacted'
USER_ID_LENGTH = 18
DAILY_CASE_LOCATION = 3
TOTAL_CASE_LOCATION = 7
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
    print('------')

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
                    await user.send("Infections case count increased by " + data[DAILY_CASE_LOCATION] + " on " + latestDataDate\
                        + " to a total of " + data[TOTAL_CASE_LOCATION] + "cases.")
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
    print("Bot ready")

'''
Bot command stats will return the testing information.
'''
@bot.command()
async def stats(ctx):
    """Returns status of BU's testing data."""

    # Construct the embed containing appropriate values.
    embed=discord.Embed(title="BU COVID-19 Testing Status", url="https://www.bu.edu/healthway/community-dashboard/", description="📅 Latest avaliable date: " + data[0], color=0xcc0000)
    embed.set_thumbnail(url="https://prod.wp.cdn.aws.wfu.edu/sites/224/2020/01/boston-university-logo-bu-vector-eps-free-download-logo-icons-brand-emblems-148777131548ngk.png")
    embed.add_field(name="🔬 Daily Tested:", value=data[1], inline=False)
    embed.add_field(name=":white_check_mark: Daily Negative:", value=data[2], inline=True)
    embed.add_field(name=":x: Daily Positive:", value=data[3], inline=True)
    embed.add_field(name="🤔 Daily Inconclusive:", value=data[4], inline=True)
    embed.add_field(name="🔬 Total Tested:", value=data[5], inline=False)
    embed.add_field(name=":white_check_mark: Total Negative:", value=data[6], inline=True)
    embed.add_field(name=":x: Total Positive:", value=data[7], inline=True)
    embed.add_field(name="🤔 Total Inconclusive:", value=data[8], inline=True)
    embed.add_field(name="🥺 Isolation Count:", value=data[9], inline=False)
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
        return await ctx.send("<@"+str(user.id)+">"+", you are registered to recieve updates")
    # This user wants to be removed from the subscriber list.
    else:
        registeredUsers.remove(user)
        with open('users', 'w') as userlist:
            for userEntry in registeredUsers:
                userlist.write('%s\n' % userEntry.id)
        userlist.close()
        return await ctx.send("<@"+str(user.id)+">"+", you have been removed from recieving updates")

'''
Start background task and start bot.
'''
updateDashboard.start()
bot.run(TOKEN)
