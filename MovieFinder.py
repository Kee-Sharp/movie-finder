#Finding movies associated with a list of names and specified genres
import requests
import time
import json
import copy
import csv
import utils
import pathlib

def main(args):
    # TMDb Base Url and API key
    URL = "https://api.themoviedb.org/3"
    key = "bed5288deb39663ad0bb3a8ed2625f4a"
    log = { "lines": [] }
    nameFile = inp("What file contains your list of names? (include extension) Or type 'manual' to enter names manually.", log)
    # Handles potential errors with user input for the file
    while nameFile != "manual" and nameFile != "done":
        if not pathlib.os.path.exists(nameFile):
            nameFile = inp("File not recognized. Try again or type 'manual' to enter names manually.", log)
        elif ".txt" not in nameFile:
            nameFile = inp("File is not a text file. Try again or type 'manual' to enter names manually.", log)
        else:
            with open(nameFile, "r") as nF:
                names = [name.strip() for name in nF.readlines()]
            log["inputNames"] = nameFile.lower()
            nameFile = "done"
    # If this option is chosen, the user will enter names one by one
    if nameFile == "manual":
        log["inputNames"] = "manual"
        names = []
        name = inp("Type each name and then press enter. Entering names will stop when you press enter twice.", log)
        while len(name):
            names.append(name)
            name = inp("", log, saveS=False, end="")
    # Base payload that will be used for each name
    payload = {"api_key": key, "include_adult": False, "language": "en-US"}
    count = 1
    nameToIds = {}
    print("Searching TMDB for people...")
    # Loop through each name in the list, searching TMDb for associated ids.
    # Assumes the correct person is the first search result for the name.
    for i, name in enumerate(names):
        # TMDb API only allows 40 requests per 10 seconds
        if count % 40 == 39:
            time.sleep(10)
        payload["query"] = name
        result = requests.get(URL+"/search/person", params=payload).json()
        if len(result['results']) and not (name in nameToIds):
            nameToIds[name] = result['results'][0]['id']
        utils.showProgress(i+1, len(names))
        count += 1
    nameToMovies = {}
    masterMovieList = []
    # Base movie payload used for each movie
    movie_payload = {'api_key': key}
    searchType, nameField = ("crew", "crew_member") if inp("Searching actors or directors?", log) == "directors" else ("cast", "actor/actress") 
    with open("genres.json", "r") as gF:
        genres = json.loads(gF.read())
    searchGenres = []
    genre = inp("Any particular genre to search? Type 'done' if no.", log).lower()
    # Handles pottential errors with user input for searching genres
    while genre != "done":
        if genre not in genres:
            genre = inp("Genre not recognized. Try again or type 'done' to continue.", log).lower()
        else:
            searchGenres.append(genre)
            genre = inp("Add another genre or type 'done' to continue.", log).lower()
    genreIds = ",".join([str(genres[g]) for g in searchGenres])
    movie_payload["with_genres"] = genreIds
    print("Getting movie details...")
    # first searches for the first 20 movies with the given genres and cast/crew member
    # then for each of those movies, requests the more detailed version
    for i, n in enumerate(nameToIds):
        if count % 40 == 39:
            time.sleep(10)
        movie_payload['with_'+searchType] = nameToIds[n]
        results = requests.get(URL+'/discover/movie', params=movie_payload).json()['results']
        count += 1
        movieDetails = []
        detail_payload = {'api_key': key, 'language': 'en-US'}
        for r in results:
            if count % 40 == 39:
                time.sleep(10)
            rawDetail = requests.get(URL+f"/movie/{r['id']}", params=detail_payload).json()
            # chooses only specific fields from the result and performs some corrections
            detail = {k: rawDetail[k] for k in rawDetail if k in ['id', 'belongs_to_collection', 'budget', 'genres', 'release_date', 'revenue', 'runtime', 'title']}
            detail['belongs_to_collection'] = detail['belongs_to_collection'] != None
            detail['genres'] = [g['name'] for g in detail['genres']]
            movieDetails.append(detail)
            masterDetail = copy.deepcopy(detail)
            masterDetail[nameField] = n
            masterMovieList.append(masterDetail)
            count += 1
        nameToMovies[n] = {'id': nameToIds[n], 'results': movieDetails}
        utils.showProgress(i+1, len(nameToIds))
    log["count"] = len(masterMovieList)
    output = inp("What name should the csv and json files be saved under?", log)
    time.sleep(0.8)
    # Creates output folder and adds the csv file with all of the relevant detail + the json file with 
    # the nameToMovies dictionary for reference
    if not pathlib.os.path.exists("output"):
        pathlib.Path("output").mkdir()
    with open(f"output/{output}.json", "w") as f1:
        f1.write(json.dumps(nameToMovies))
    with open(f"output/{output}.csv", "w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["id", "title","release_date","budget", "revenue", nameField, "genres", "belongs_to_collection","runtime"], extrasaction="ignore")
        writer.writeheader()
        for m in masterMovieList:
            writer.writerow(m)
    with open(f"output/{output}.log", "w") as f2:
        p1 = "names inputted at run time" if log["inputNames"] == "manual" else log["inputNames"]
        if not len(searchGenres):
            p2 = "no search genres" 
        elif len(searchGenres) == 1:
            p2 = f"{searchGenres[0]} as a search genre"
        else:
            p2 = f"{', '.join(searchGenres[0:-1])} and {searchGenres[-1]} as search genres"
        p3 = log["count"]
        f2.write(f"Application run on {p1} using {p2} with {p3} result(s)\n\n")
        f2.write("Program lines: \n")
        for line in log["lines"]:
            f2.write(line+"\n")

def inp(s, log, saveS=True, end="\n"):
    """Input function wrapper to save input and prompt to log file"""
    val = input(s+end)
    if saveS:
        log["lines"].append(s)
    if len(val):
        log["lines"].append(val.strip())
    return val

if __name__ == "__main__":
    import sys
    main(sys.argv)