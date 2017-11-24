"""
Quick scipt to get all games in the database and save to text file.
"""

from bs4 import BeautifulSoup
from urllib2 import urlopen


def scrape():
    page = urlopen(('https://github.com/sealneaward/'
                    'nba-movement-data/tree/master/data')).read()
    soup = BeautifulSoup(page)
    f = open('allgames.txt', 'w')
    for anchor in soup.findAll('a', class_="js-navigation-open"):
        if anchor.text.endswith('.7z') and len(anchor.text) == 24:
            f.write(anchor.text + '\n')
    f.close()
    return


if __name__ == '__main__':
    scrape()
