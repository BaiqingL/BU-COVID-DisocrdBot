# Import web driver code.
import time, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Constants.
ESTIMATED_DATA_LENGTH = 1300
DASHBOARD_LINK = "https://app.powerbi.com/view?r=eyJrIjoiMzI4OTBlMzgtODg5MC00OGEwLThlMDItNGJiNDdjMDU5ODhkIiwidCI6ImQ1N2QzMmNjLWMxMjEtNDg4Zi1iMDdiLWRmZTcwNTY4MGM3MSIsImMiOjN9"

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
    driver.get(DASHBOARD_LINK)
    # We are looking for reportLandingContainer, wait for the page to populate with proper results before exiting.
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
    dateEndIndex = rawDataSegment.rfind("Negative Tests")
    dateBeginIndex = rawDataSegment.rfind('\n',0,dateEndIndex-1)
    date = rawDataSegment[dateBeginIndex+1:dateEndIndex-1]

    # Find how many tests were done in a day.
    dailyTestEndIndex = rawDataSegment.find("Test Results*")
    dailyTestBeginIndex = rawDataSegment.rfind('\n',0,dailyTestEndIndex-1)
    dailyTestConducted = re.sub("[^0-9]", "", rawDataSegment[dailyTestBeginIndex+1:dailyTestEndIndex-1])
    # Find how many tests were negative in day.
    dailyNegativeEndIndex = rawDataSegment.find("Negative Tests", dailyTestEndIndex)
    dailyNegativeBeginIndex = rawDataSegment.rfind('\n',0,dailyNegativeEndIndex-1)
    dailyNegativeOutcome = re.sub("[^0-9]", "", rawDataSegment[dailyNegativeBeginIndex+1:dailyNegativeEndIndex-1])
    # Find how many tests were positive in a day.
    dailyPositiveEndIndex = rawDataSegment.find("Positive Tests", dailyNegativeEndIndex)
    dailyPositiveBeginIndex = rawDataSegment.rfind('\n',0,dailyPositiveEndIndex-1)
    dailyPositiveOutcome = re.sub("[^0-9]", "", rawDataSegment[dailyPositiveBeginIndex+1:dailyPositiveEndIndex-1])
    # Find how many test were inconclusive.
    dailyInconclusiveOutcome = str(int(dailyTestConducted.replace(',','')) - \
        int(dailyNegativeOutcome.replace(',','')) - int(dailyPositiveOutcome.replace(',','')))

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
    totalInconclusiveOutcome = str(int(totalTestConducted.replace(',','')) - \
        int(totalNegativeOutcome.replace(',','')) - int(totalPositiveOutcome.replace(',','')))

    # Find how many students are in isolation.
    isolationCountEndIndex = rawDataSegment.find("Currently in Isolation")
    isolationCountBeginIndex = rawDataSegment.rfind('\n',0,isolationCountEndIndex-1)
    isolationCount = rawDataSegment[isolationCountBeginIndex+1:isolationCountEndIndex-1]

    # Find how many students have recovered
    recoveredCountEndIndex = rawDataSegment.find("Recovered")
    recoveredCountBeginIndex = rawDataSegment.rfind('\n',0,recoveredCountEndIndex-1)
    recoveredCount = rawDataSegment[recoveredCountBeginIndex+1:recoveredCountEndIndex-1]

    # Find confirmed noncontagious count
    confirmedNoncontagiousCountEndIndex = rawDataSegment.find("Confirmed Noncontagious")
    confirmedNoncontagiousCountBeginIndex = rawDataSegment.rfind('\n',0,confirmedNoncontagiousCountEndIndex-1)
    confirmedNoncontagiousCount = rawDataSegment[confirmedNoncontagiousCountBeginIndex+1:confirmedNoncontagiousCountEndIndex-1]

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
        isolationCount,
        recoveredCount,
        confirmedNoncontagiousCount
        ]

'''
Make the data look nicer in the backend.
'''
def backendReport(data):
    print("\n")
    print("Latest Date: " + data[0])
    print("Daily: " + data[1])
    print("Daily Negative: " + data[2])
    print("Daily Positive: " + data[3])
    print("Total: " + data[5])
    print("Total Negative: " + data[6])
    print("Total Positive: " + data[7])
    print("Isolation Count: " + data[9])
    print("Recovered Count: " + data[10])
    print("----------------------------")
