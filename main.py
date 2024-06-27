import requests as rq
from bs4 import BeautifulSoup

URL = 'https://happilylover.com/love-letters/'


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


if __name__ == '__main__':
    my_request = rq.get(URL)
    print(my_request.status_code)
    print(type(my_request))
# print(my_request.text)
