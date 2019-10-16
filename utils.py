import requests
import time
from bs4 import BeautifulSoup

def showProgress(i, length, size=50):
    """Will print an updating progress bar as i goes from 0 to length"""
    n = "\n"
    r = "\r"
    string1 = (int(size*i/length)*"#")+(int(size*(length-i)/length)*'_') 
    string2 = "%.1f" % (100*i/length)
    print(f"[{string1}]  {string2}% Completed", end=f"{n if i == length else r}")

def get_list(url, paths):
    """Extracts a list of items from url making use of an array of paths to the given items.
    Paths is a list of lists of css selectors, i.e [[div#id.className1.className2, p]]"""
    doc = requests.get(url).text
    soup = BeautifulSoup(doc, "html.parser")
    names = []
    for path in paths:
        enclosing = path[0]
        arr = soup.select(enclosing)
        del path[0]
        while len(path):
                arr = [a.select(path[0])[0] for a in arr]
                del path[0]
        n = [a.text.strip() for a in arr]
        names.extend(n)
    return names

def list_representation(l):
    """Returns a string representation of a list, without oxford comma.
    [a,b,c,d] => 'a, b, c and d' """
    return f"{', '.join(l[0:-1])} and {l[-1]}"