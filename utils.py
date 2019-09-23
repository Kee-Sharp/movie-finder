import requests
import time
from bs4 import BeautifulSoup

def showProgress(i, length, size=50):
    n = "\n"
    r = "\r"
    string1 = (int(size*i/length)*"#")+(int(size*(length-i)/length)*'_') 
    string2 = "%.1f" % (100*i/length)
    print(f"[{string1}]  {string2}% Completed", end=f"{n if i == length else r}")
#     print("\033[F", end=r)
#     print("\033[K", end=r)
#     for s in ["This is a longer string", "a", "b", "c", "d", "e"]:
#         print(s, end="\r")
#         time.sleep(1)
#         print("\033[F", end="\r")
#         time.sleep(1)
#         print("\033[K", end="\r")
#         time.sleep(1)

#path is a list of lists of css selector, i.e div#id.className1.className2
def get_list(url, paths):
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