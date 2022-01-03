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

def list_representation(l):
    """Returns a string representation of a list, without oxford comma.
    [a,b,c,d] => 'a, b, c and d' """
    return f"{', '.join(l[0:-1])} and {l[-1]}" if len(l) - 1 else l[0]

def inp(s, log, saveS=True, end="\n"):
    """Input function wrapper to save input and prompt to log file"""
    val = input(s+end).strip()
    if saveS:
        log["lines"].append(s)
    if len(val):
        log["lines"].append(val)
    return val.lower()

def onlyKeys(d, keys):
    """Reduces d so that each key in d is in keys"""
    return {k:v for k,v in d.items() if k in keys}
    
def rmKeys(d,keys):
    """Removes each key in keys from dict d"""
    return {k:v for k,v in d.items() if k not in keys}