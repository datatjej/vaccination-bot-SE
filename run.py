# Import necessary packages
import re
import tweepy
import requests
import pandas as pd
import configargparse as cap
from bs4 import BeautifulSoup

# Site URL
url="https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/statistik-och-analyser/statistik-over-registrerade-vaccinationer-covid-19/"

# Make a GET request to fetch the raw HTML content
html_content = requests.get(url).text

# Parse HTML code for the entire site
soup = BeautifulSoup(html_content, "html5lib")
#print(soup.prettify()) # print the parsed data of html

# Get the right table by sorting on caption
table2 = soup.find("caption", text="Tabell 2. Antal och andel vaccinerade med minst 1 dos respektive 2 doser").find_parent("table")

# Lets go ahead and scrape first table with HTML code gdp[0]
# OLD: table1 = gdp[0]
# the head will form our column names
body = table2.find_all("tr")
# Head values (Column names) are the first items of the body list
head = body[0] # 0th item is the header row
body_rows = body[1:] # All other items becomes the rest of the rows

# Lets now iterate through the head HTML code and make list of clean headings

# Declare empty list to keep Columns names
headings = []
for item in head.find_all("th"): # loop through all th elements
    # convert the th elements to text and strip "\n"
    item = (item.text) #.rstrip("\n")
    # append the clean column name to headings
    headings.append(item)
#print(headings)

# Next is now to loop though the rest of the rows

all_rows = [] # will be a list for list for all rows
for row_num in range(len(body_rows)): # A row at a time
    row = [] # this will old entries for one row
    for index, row_item in enumerate(body_rows[row_num].find_all("td")): #loop through all row entries
        # row_item.text removes the tags from the entries
        if index == 0:
            date = row_item.text
            row.append(date)
        elif index == 1 or index == 3:
            number = int(re.sub("(\s)","",row_item.text))
            row.append(number)
        elif index == 2 or index == 4:
            percentage = float(re.sub(",",".",row_item.text))
            row.append(percentage)
    # append one row to all_rows
    all_rows.append(row)

# We can now use the data on all_rowsa and headings to make a table
# all_rows becomes our data and headings the column names
df = pd.DataFrame(data=all_rows,columns=headings)
#print(df)

#adult_population = 8189892 # SCB's adult population figure from 31-12-2020

percentage_first_dose = df['Andel (%) vaccinerademed minst 1 dos'].values[0]
percentage_second_dose = df['Andel (%) vaccinerademed 2 doser'].values[0]
first_bar = "[" + '█' * int(percentage_first_dose/3) + "." * int((100-percentage_first_dose)/3) + "] " + str(percentage_first_dose) + " %"
second_bar = "[" + '█' * int(percentage_second_dose/3) + "." * int((100-percentage_second_dose)/3) + "] " + str(percentage_second_dose) + " %"

tweet_string = "Första dosen:" + "\n" + first_bar + "\n\n" + "Andra dosen:" + "\n" + second_bar

argparser = cap.ArgParser(default_config_files=['keys.yml'])
argparser.add('-c', is_config_file=True, help='config file path')
argparser.add('--api', env_var='BOT_API')
argparser.add('--api-secret', env_var='BOT_API_SECRET')
argparser.add('--access', env_var='BOT_ACCESS')
argparser.add('--access-secret', env_var='BOT_ACCESS_SECRET')

args = argparser.parse_args()

# Authenticate to Twitter
auth = tweepy.OAuthHandler(args.api, args.api_secret)
auth.set_access_token(args.access, args.access_secret)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

try:
    api.verify_credentials()
    print("Authentication OK")
except:
    print("Error during authentication")

api.update_status(tweet_string)
