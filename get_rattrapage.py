# -*- coding: utf-8 -*-
"""
Created on Sat Jul  6 11:41:22 2024
@author: labrecquev
Radio-Canada Premiere rattrapage
"""

import requests
from bs4 import BeautifulSoup
import dateparser
import os
from datetime import datetime
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from pathlib import Path

now = datetime.now()
now_str = now.strftime("%Y%m%d")

radio_shows = {"Les années lumière":"https://ici.radio-canada.ca/ohdio/premiere/emissions/52/les-annees-lumiere",
                "Les grands entretiens":"https://ici.radio-canada.ca/ohdio/premiere/emissions/4586/les-grands-entretiens",
                "Les faits d'abord":"https://ici.radio-canada.ca/ohdio/premiere/emissions/6897/les-faits-dabord",
                "Le genre humain":"https://ici.radio-canada.ca/ohdio/premiere/emissions/8582/genre-humain",
                "Ça nous regarde":"https://ici.radio-canada.ca/ohdio/premiere/emissions/11018/ca-nous-regarde",
                "Dessine-moi un matin":"https://ici.radio-canada.ca/ohdio/premiere/emissions/9906/dessine-moi-un-matin",
                "Feu vert":"https://ici.radio-canada.ca/ohdio/premiere/emissions/4604/feu-vert",
                "Moteur de recherche":"https://ici.radio-canada.ca/ohdio/premiere/emissions/6056/moteur-de-recherche",
                "Passion politique":"https://ici.radio-canada.ca/ohdio/premiere/emissions/10916/passion-politique",
                "Tout terrain":"https://ici.radio-canada.ca/ohdio/premiere/emissions/11019/tout-terrain"
                }

def main():
    start = datetime.now()
    print(f"Script start, retrieving today's shows. It is {datetime.now()}")
    # Load .env file
    load_dotenv(override=True)
    # get credentials
    pwd = os.getenv('MY_PASSWORD')
    temp_dir = Path(os.getenv('TEMP_DIR'))
    mail_user = os.getenv('MAIL_USER')
    mail_list = os.getenv('MAIL_LIST')

    rattrapage_data = get_rattrapage_data(temp_dir)
    send_email_summary(rattrapage_data, mail_user, mail_list, pwd)
    
    duration = datetime.now() - start
    
    print(f"Script done, it took {duration}")

def french_date_parser(string):
    # Define the regex pattern for French dates
    pattern = r'\b([1-9]|[12][0-9]|3[01])\s(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|avr.|juill.|févr.|janv.|déc.|nov.|oct.|sept.)\s(\d{4})\b'
    date_pattern = re.compile(pattern, re.IGNORECASE)
    match = date_pattern.search(string)
    raw_date = match.group().replace('juill.', 'juillet')
    parsed_date = dateparser.parse(raw_date)
    if parsed_date:
        return parsed_date
    else:
        print(f"Could not parse date from:\n{string}")
    
def get_rattrapage_data(temp_dir):
    rattrapage_data = {}
    
    for name, url in radio_shows.items():
        print(f"\n{name}\n{url}")
        tempfile = os.path.join(temp_dir, f"{name}_{now_str}.html")
        
        if os.path.exists(tempfile):
            print("\tfile detected, reading the local file")
            with open(tempfile, 'r', encoding='utf-8') as file:
                response = file.read()
        else:
            print("\tno file to read, requesting webpage")
            response = requests.get(url)
            
            if response.status_code == 200:
                # Save response content to an HTML file
                with open(tempfile, 'wb') as f:
                    f.write(response.content)
                print("\tHTML file saved successfully.")
                response = response.text
            else:
                print(f"\tFailed to retrieve HTML: {response.status_code}")
        
        soup = BeautifulSoup(response, 'html.parser')
        
        emissions = soup.find('ul', class_='list-section-menu-list')
    
        li_items = emissions.find_all('li')
        for li in li_items:
            h_tag = li.find('h2')
            if h_tag:            
                a_tag = li.find('a')
                if a_tag:
                    link_text = a_tag.text.strip()            
                    parsed_date = french_date_parser(link_text)
                    if parsed_date:
                        href = a_tag.get('href')
                        emission_url = f"https://ici.radio-canada.ca{href}"
                        if parsed_date.date() == now.date():
                            print(f"\t\tInserting {parsed_date.date()}'s show into dict")
                            text_subtitle = li.find('span', class_='text subtitle')
                            if text_subtitle:
                                text_subtitle = text_subtitle.text.strip()
                                rattrapage_data[name] = [emission_url, text_subtitle]
                                break
    return rattrapage_data

def send_email_summary(rattrapage_data, mail_user, mail_list, pwd):
    print(f"{mail_user=}, {mail_list=}, {pwd=}")
    # Initialize an empty string to hold the HTML content
    html_content = "<ul>\n"
    
    # Iterate over the dictionary to build the HTML list
    for name, (url, subtitle) in rattrapage_data.items():
        html_content += "  <li>\n"
        html_content += f"    <a href='{url}'>{name}</a>\n"
        html_content += "    <ul>\n"
        html_content += f"      <li>{subtitle}</li>\n"
        html_content += "    </ul>\n"
        html_content += "  </li>\n"
    
    # Close the unordered list tag
    html_content += "</ul>"
    
    # Email parameters
    sent_from = mail_user
    sent_to = mail_list    
    subject = f"Rattrapage Radio-Canada du {now.date()}"
    
    # Create the MIME message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sent_from
    msg['To'] = sent_to
    
    
    # Attach the HTML content
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Send the email using SMTP
    try:
        server = smtplib.SMTP_SSL('mail.labrecquev.ca', 465)
        server.ehlo()
        server.login(mail_user, pwd)
        server.sendmail(sent_from, sent_to, msg.as_string())
        server.quit()
        print("Email sent!")
    except Exception as err:
        print(f"Email not sent\n{err}")

if __name__ == "__main__":
    main()