import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import string
import re
import datetime
import sqlite3
import time

all_links = []
e_name = []
f1 = []
f2 = []


def scrape_data():
    data = requests.get("http://ufcstats.com/statistics/events/upcoming")
    soup = BeautifulSoup(data.text, 'html.parser')
    table = soup.find('table', {"class": "b-statistics__table-events"})
    links = table.find_all('a', href=True)

    for link in links:
        all_links.append(link.get('href'))

    for link in all_links:
        print(f"Now currently scraping link: {link}")

        data = requests.get(link)
        soup = BeautifulSoup(data.text, 'html.parser')
        time.sleep(1)

        rows = soup.find_all('tr', {
            "class": "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"})

        for row in rows:

            h2 = soup.find("h2")
            e_name.append(h2.text.strip())

            fighters = row.find_all('a', {"href": re.compile("http://ufcstats.com/fighter-details")})

            try:
                f1.append(fighters[0].text.strip())
                f2.append(fighters[1].text.strip())
            except IndexError:
                f1.append("null")
                f2.append("null")
            continue

    return None


# preprocessing
# remove rows where DOB is null
# impute stance as orthodox for missing stances
def create_df():
    # create empty dataframe
    df = pd.DataFrame()

    df["Event"] = e_name
    df["Fighter_1"] = f1
    df["Fighter_2"] = f2

    return df


def merge_data(df):


        # We're always asking for json because it's the easiest to deal with
        morph_api_url = "https://api.morph.io/rdmaloney/odds_scraper/data.json"

        # Keep this key secret!
        morph_api_key = "/y3liZqj/BLyw2JBNNXW"

        r = requests.get(morph_api_url, params={
            'key': morph_api_key,
            'query': "select * from data"
        })
        
        j = r.json()

        odds_db = pd.DataFrame.from_dict(j)

        
        test = pd.merge(df, odds_db, left_on=["Fighter_1", "Fighter_2"], right_on=["Fighter1", "Fighter2"])
        '''
        test2 = pd.merge(test, odds_db, left_on=["Fighter_2"], right_on=["Fighter2"])
        test3= pd.concat([test2,odds_db],axis=1,sort=True)
 
        '''
        final_df = test[['Event', 'Fighter_1', 'Fighter_2', 'Fighter1_Odds', 'Fighter2_Odds']]

        return final_df
        
        
        return test
        
scrape_data()
df = create_df()
df = merge_data(df)

conn = sqlite3.connect('data.sqlite')
df.to_sql('data', conn, if_exists='replace')
print('Db successfully constructed and saved')
conn.close()
