# Import web driver code
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Constants
ESTIMATED_DATA_LENGTH = 1300

def getDriver():
    '''
    Initiate a driver instance of the chrome web browser to render the javascript
    '''
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def getRawData(driver):
    '''
    Since BU uses Microsoft Power BI to display data, it is a javascript driven page.
    This means we need to use selenium to properly render and grab data.
    '''
    driver.get('https://app.powerbi.com/view?r=eyJrIjoiMzI4OTBlMzgtODg5MC00OGEwLThlMDItNGJiNDdjMDU5ODhkIiwidCI6ImQ1N2QzMmNjLWMxMjEtNDg4Zi1iMDdiLWRmZTcwNTY4MGM3MSIsImMiOjN9')
    # We are looking for reportLandingContainer
    rawDataSegment = ""
    while len(rawDataSegment) < ESTIMATED_DATA_LENGTH:
        rawDataSegment = driver.find_element_by_id('reportLandingContainer').text
    driver.quit()
    return rawDataSegment

def processData(rawDataSegment):
    '''
    String manipulation to parse data
    '''

    # Find date of the latest data
    dateEndIndex = rawDataSegment.find("Positive")
    dateBeginIndex = rawDataSegment.rfind('\n',0,dateEndIndex-1)
    date = rawDataSegment[dateBeginIndex+1:dateEndIndex-1]

    # Find how many tests were done in a day
    dailyTestEndIndex = rawDataSegment.find("Test Results")
    dailyTestBeginIndex = rawDataSegment.rfind('\n',0,dailyTestEndIndex-1)
    dailyTestConducted = rawDataSegment[dailyTestBeginIndex+1:dailyTestEndIndex-1]

    # Find how many tests were negative in day
    dailyNegativeEndIndex = rawDataSegment.find("Negative Tests")
    dailyNegativeBeginIndex = rawDataSegment.rfind('\n',0,dailyNegativeEndIndex-1)
    dailyNegativeOutcome = rawDataSegment[dailyNegativeBeginIndex+1:dailyNegativeEndIndex-1]

    # Find how many tests were positive in a day
    dailyPositiveEndIndex = rawDataSegment.find("Positive Tests")
    dailyPositiveBeginIndex = rawDataSegment.rfind('\n',0,dailyPositiveEndIndex-1)
    dailyPositiveOutcome = rawDataSegment[dailyPositiveBeginIndex+1:dailyPositiveEndIndex-1]

    # Find how many test were inconclusive
    dailyInconclusiveOutcome = str(int(dailyTestConducted.replace(',','')) - int(dailyNegativeOutcome.replace(',','')) - int(dailyPositiveOutcome.replace(',','')))

    # Find how many tests were done in total
    totalTestEndIndex = rawDataSegment.find("Test Results", dailyTestEndIndex+1)
    totalTestBeginIndex = rawDataSegment.rfind('\n',0,totalTestEndIndex-1)
    totalTestConducted = rawDataSegment[totalTestBeginIndex+1:totalTestEndIndex-1]

    # Find how many tests were negative in total
    totalNegativeEndIndex = rawDataSegment.find("Negative Tests", dailyNegativeEndIndex+1)
    totalNegativeBeginIndex = rawDataSegment.rfind('\n',0,totalNegativeEndIndex-1)
    totalNegativeOutcome = rawDataSegment[totalNegativeBeginIndex+1:totalNegativeEndIndex-1]

    # Find how many tests were positive in total
    totalPositiveEndIndex = rawDataSegment.find("Positive Tests", dailyPositiveEndIndex+1)
    totalPositiveBeginIndex = rawDataSegment.rfind('\n',0,totalPositiveEndIndex-1)
    totalPositiveOutcome = rawDataSegment[totalPositiveBeginIndex+1:totalPositiveEndIndex-1]

    # Find how many test were inconclusive
    totalInconclusiveOutcome = str(int(totalTestConducted.replace(',','')) - int(totalNegativeOutcome.replace(',','')) - int(totalPositiveOutcome.replace(',','')))

    # Find how many students are in isolation
    isolationCountEndIndex = rawDataSegment.find("Currently in Isolation")
    isolationCountBeginIndex = rawDataSegment.rfind('\n',0,isolationCountEndIndex-1)
    isolationCount = rawDataSegment[isolationCountBeginIndex+1:isolationCountEndIndex-1]

    '''
    print("📅 Latest Date: " + date)
    print("\n")
    print("🔬 Daily: " + dailyTestConducted)
    print("✔️ Daily Negative: " + dailyNegativeOutcome)
    print("🤒 Daily Positive: " + dailyPositiveOutcome)
    print("🤔 Daily Inconclusive: " + dailyInconclusiveOutcome)
    print("\n")
    print("🔬 Total: " + totalTestConducted)
    print("✔️ Total Negative: " + totalNegativeOutcome)
    print("🤒 Total Positive: " + totalPositiveOutcome)
    print("🤔 Total Inconclusive: " + totalInconclusiveOutcome)
    print("\n")
    print("🥺 Isolation Count: " + isolationCount)
    '''
    # Data array constructed with below values
    return [date,dailyTestConducted,dailyNegativeOutcome,dailyPositiveOutcome,dailyInconclusiveOutcome,totalTestConducted,totalNegativeOutcome,totalPositiveOutcome,totalInconclusiveOutcome,isolationCount]

'''
Data extraction part complete, discord part below
Example code skeleton structure from: https://github.com/Rapptz/discord.py/blob/master/examples/basic_bot.py
'''
# Discord related imports
import discord, asyncio, datetime
from discord.ext import commands, tasks

# Constants and bot initilization
TOKEN = 'Discord Bot Token Redacted'
description = '''A bot to streamline the COVID-19 stats from the BU testing dashboard'''
bot = commands.Bot(command_prefix='?', description=description)

# Gather initial testing data
driver = getDriver()
rawData = getRawData(driver)
data = processData(rawData)
lastChecked = datetime.datetime.now()

# Update the values in the background
def updateValues():
    # Probably not a great idea but it works
    global data
    driver = getDriver()
    rawData = getRawData(driver)
    data = processData(rawData)
    return data

# Display bot information in the backend
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

# Background task to call update every 10 minutes
@tasks.loop(minutes=10.0)
async def updateDashboard():
    updateValues()
    # Report data array to the backend, consult processData() for value meaning
    print(data)

# Bot command stats will return the testing information
@bot.command()
async def stats(ctx):
    """Returns status of BU's testing data"""

    # Construct the embed containing appropriate values
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

updateDashboard.start()
bot.run(TOKEN)
