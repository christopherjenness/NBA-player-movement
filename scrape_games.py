from bs4 import BeautifulSoup
from urllib.request import urlopen

page = urlopen('https://github.com/neilmj/BasketballData/tree/master/2016.NBA.Raw.SportVU.Game.Logs').read()
soup = BeautifulSoup(page)

for anchor in soup.findAll('a', class_="js-navigation-open" ):
    print (anchor)