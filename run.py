# Import necessary packages
import re
import tweepy
import requests
import pandas as pd
import configargparse as cap
from bs4 import BeautifulSoup

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

# Site URL
url="https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/statistik-och-analyser/statistik-over-registrerade-vaccinationer-covid-19/"

# Make a GET request to fetch the raw HTML content
html_content = requests.get(url).text

# Parse HTML code for the entire site
soup = BeautifulSoup(html_content, "html5lib")
#print(soup.prettify()) # print the parsed data of html

# Get the right table by sorting on caption
table2 = soup.find("caption", text="Tabell 2. Antal och andel vaccinerade med minst 1 dos respektive 2 doser.").find_parent("table")

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
    #rint(item)
    # append the clean column name to headings
    headings.append(item)

# Next is now to loop though the rest of the rows

all_rows = [] # will be a list for list for all rows
#print("body rows: ", body_rows)
for row_num in range(len(body_rows)): # A row at a time
    row = [] # this will old entries for one row
    date = body_rows[row_num].find('th') # extract the date from the header cell in each row
    row.append(date.get_text())
    for index, row_item in enumerate(body_rows[row_num].find_all("td")): # loop through all remaining row cells on each line
        if index == 0 or index == 2:
            number = int(re.sub("(\s)","",row_item.text)) # get the de facto number of people vaccinated (not currently used for the tweet)   
            row.append(number)
        elif index == 1 or index == 3:
            percentage_without_sign = re.sub("%","",row_item.text) # get the percentage without % sign
            percentage_without_comma = float(re.sub(",",".",percentage_without_sign)) # ...and replace comma with point notation
            row.append(percentage_without_comma)
    # append one row to all_rows
    all_rows.append(row)

# We can now use the data on all_rowsa and headings to make a table
# all_rows becomes our data and headings the column names
df = pd.DataFrame(data=all_rows,columns=headings)
print(df)

percentage_first_dose = df['Andel (%) vaccinerademed minst 1 dos'].values[0]
percentage_second_dose = df['Andel (%) vaccinerademed 2 doser'].values[0]

first_bar = "[" + '▓' * int(percentage_first_dose/5) + "░" * int((100-percentage_first_dose)/5) + "] " + str(percentage_first_dose) + " %"
second_bar = "[" + '▓' * int(percentage_second_dose/5) + "░" * int((100-percentage_second_dose)/5) + "] " + str(percentage_second_dose) + " %"

tweet_string = "Första dosen:" + "\n" + first_bar + "\n\n" + "Andra dosen:" + "\n" + second_bar
print(tweet_string)

# Tweet progress bars of statistics as string (duplicates of previously tweeted messages not allowed)
api.update_status(tweet_string)