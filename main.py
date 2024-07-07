import smtplib
import ssl
import sys
from datetime import date, timedelta
from email.message import EmailMessage
from typing import Any
import logging

import bs4
import keyring as kr
import numpy as np
import pandas as pd
import requests as rq
from bs4 import BeautifulSoup, ResultSet

# Globals
URL = 'https://happilylover.com/love-letters/'
SUBJECT = 'To My Love'
FROM = 'jtweedle1992@gmail.com'
TO = 'myeryar@wpsdk12.org'
PORT = 465
SERVICE_NAME = 'GMAIL'
INPUT = './data/input.xlsx'
FILENAME = f'./logs/{date.today()}.log'
LOGGER = logging.getLogger(__name__)

def setup_logger(filename: str):
    logging.basicConfig(filename=filename, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def credentials(service_name: str = SERVICE_NAME, username: str = FROM) -> str:
    """
    Get password from windows credential manager
    :param service_name: website or application name
    :param username: associated username
    :return: password
    """
    return kr.get_password(service_name, username)


def get(url: str) -> rq.models.Response:
    """
    get request to url
    :param url: url
    :return: request response
    """
    try:
        r = rq.get(url)
        r.raise_for_status()
        return r
    except rq.exceptions.ConnectionError as err:
        # eg, no internet
        raise SystemExit(err)
    except rq.exceptions.HTTPError as err:
        # eg, url, server and other errors
        raise SystemExit(err)


def parse(text: bytes) -> bs4.BeautifulSoup:
    """
    Parsed html of text
    :param text: text to parse
    :return: parsed html
    """
    return BeautifulSoup(text, 'html.parser')


def find_text(parsed_html: bs4.BeautifulSoup, tag: str, class_: str = None) -> list:
    """
    All text under <tag> class = class_
    :param parsed_html:
    :param tag: tag
    :param class_: class
    :return: text
    """
    return [item.get_text().strip() for item in parsed_html.find_all(tag, class_)]


def find_tags(parsed_html: bs4.BeautifulSoup, tag: str, class_: str = None) -> ResultSet[Any]:
    return parsed_html.find_all(tag, class_)


def random_dates(start: date, end: date, n: int, seed: int = None) -> list:
    """
    generate a chronologically ordered list of random dates between start and end
    :param start: start date
    :param end: end date
    :param n: number of dates
    :param seed: seed generator
    :return: list of randomly generated dates
    """
    if seed is not None:
        np.random.seed(seed)
    days_diff = (end - start).days
    rand_days = np.sort(np.random.choice(days_diff, n, replace=False))
    return [start + timedelta(days=int(day)) for day in rand_days]


def generate_data(titles: bs4.element.ResultSet) -> pd.DataFrame:
    """
    Given an unordered list(as html tags)  from a webpage, find all paragraphs between each title
    :param titles: <ul> tag titles
    :return: a dataframe that matches each title with its associated paragraph and a random date
    """
    love_letters = {}
    for title in titles:
        love_letters.setdefault(title.get_text().strip().lower(), [])
        next_sibling = title.find_next_sibling()
        while next_sibling is not None and next_sibling.name != title.name:
            if next_sibling.name == 'p':
                love_letters[title.get_text().strip().lower()].append(next_sibling.get_text().strip().lower())
            next_sibling = next_sibling.find_next_sibling()
    love_letters = pd.DataFrame(data={key: '.\n'.join(value) for key, value in love_letters.items()}.items(),
                                columns=['title', 'letter'])
    ran = random_dates(date.today(), date(2024, 10, 11), 18, 1)
    love_letters['date'] = ran
    return love_letters


def first_main():
    """
    Run once and only once to scrape love letters from global URL website and write to excel
    """
    my_request = rq.get(URL)
    html_content = parse(my_request.content)
    titles = find_tags(html_content, 'ul', 'wp-block-list')
    love_letters = generate_data(titles)
    love_letters.to_excel(INPUT, index=False)


def send_email(content: str, sender: str = FROM, to: str = TO, subject: str = SUBJECT, port: int = PORT):
    """
    Send an email from FROM to TO with subject and content(body)
    :param content: email body
    :param sender: sending email address
    :param to: receiving email address
    :param subject: subject line
    :param port: port number
    """
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    context = ssl.create_default_context()
    password = credentials()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, to, msg.as_string())


def main():
    """
    Read first row from scraped website data, and if date matches today's date then send email with the content,
    and rewrite the data without the first row
    :return:
    """
    setup_logger(FILENAME)
    LOGGER.info(f'Starting {__name__}')
    df = pd.read_excel(INPUT)
    data = df.iloc[0]
    rand_date = data['date']
    if pd.Timestamp(date.today()) == rand_date:
        LOGGER.info(f"Today's date: {date.today()} matches random date: {rand_date}")
        payload = data['letter']
        LOGGER.info('Sending Email')
        send_email(payload)
        LOGGER.info('Writing new data')
        df.iloc[1:].to_excel(INPUT, index=False)
        LOGGER.info('Finished')
    else:
        LOGGER.info(f"Today's date: {date.today()} doesn't match random date: {rand_date}")
        sys.exit(0)


if __name__ == '__main__':
    main()
