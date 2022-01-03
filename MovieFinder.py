#Finding movies associated with a list of names and specified genres
import requests
import time
import json
import copy
import csv
from utils import *
import pathlib
import pandas as pd
pd.set_option("max_columns", 10)
pd.set_option("display.width", 200)

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
                nameLines = [nL.strip() for nL in nF.readlines()]
                nameGroups = [[name.strip() for name in nL.split(",")] for nL in nameLines]
            log["inputNames"] = nameFile.lower()
            nameFile = "done"
    # If this option is chosen, the user will enter names one by one
    if nameFile == "manual":
        log["inputNames"] = "manual"
        nameGroups = []
        nameGroup = inp("Type each name (or group of names separated by ',') and then press enter. Entering names will stop when you press enter twice.", log)
        while len(nameGroup):
            nameGroups.append([name.strip() for name in nameGroup.split(",")])
            nameGroup = inp("", log, saveS=False, end="")
    time.sleep(0.5)
    # If the cache exists, the nameToIds dict will use that as a base
    if pathlib.os.path.exists("cache.json"):
        with open("cache.json", "r") as cache:
            nameToIds = json.loads(cache.read())
    else:
        nameToIds = {}

    # Base payload that will be used for each name
    payload = {"api_key": key, "include_adult": False, "language": "en-US"}
    count = 1
    print("Searching TMDB for people...")
    time.sleep(0.5)
    # Loop through each name in the list, searching TMDb for associated ids.
    # Assumes the correct person is the first search result for the name.
    for i, nameGroup in enumerate(nameGroups):
        for name in nameGroup:
            # TMDb API only allows 40 requests per 10 seconds
            if count % 40 == 39:
                time.sleep(10)
            if name not in nameToIds:
                payload["query"] = name
                result = requests.get(URL+"/search/person", params=payload).json()
                if len(result['results']):
                    nameToIds[name] = result['results'][0]['id']
                else:
                    print(f"No results found for '{name}'")
                count += 1
        showProgress(i+1, len(nameGroups))
    # Updates the cache
    with open("cache.json", "w") as cacheWrite:
        cacheWrite.write(json.dumps(nameToIds))
    time.sleep(0.5)
    movie_payload = {'api_key': key} # Base movie payload used for each movie
    fields = {"actors": ("cast", "actors/actresses"), "directors": ("crew","crew_members"), "both": ("people","cast/crew")}
    searchType, nameField = fields[inp("Searching actors, directors, or both?", log)] 
    time.sleep(0.5)
    with open("genres.json", "r") as gF:
        genres = json.loads(gF.read())
    searchGenres = []
    genre = inp("Any particular genre to search? Type 'done' if no or type 'all' to see all available genres.", log)
    # Handles pottential errors with user input for searching genres
    while genre != "done":
        time.sleep(0.3)
        if genre == "all":
            genre = inp(f"Available genres are {list_representation(list(genres))}. Enter one of these or press 'done' to continue.", log)
        elif genre not in [g.lower() for g in genres]:
            genre = inp("Genre not recognized. Try again, type 'done' to continue, or type 'all' to see all available genres.", log)
        elif genre in searchGenres:
            genre = inp("Genre already added. Try again, type 'done' to continue, or type 'all' to see all available genres.", log)
        else:
            searchGenres.append(genre)
            genre = inp("Add another genre, type 'done' to continue, or type 'all' to see all available genres.", log)
    time.sleep(0.5)
    genreIds = [genres[g] for g in genres if g.lower() in searchGenres]
    movie_payload["with_genres"] = genreIds
    print("Getting movie details...")
    # first searches for the first 20 movies with the given genres and cast/crew members   
    # then for each of those movies, requests the more detailed version
    movies = {}
    groupToMovies = {}
    for i, nameGroup in enumerate(nameGroups):
        if count % 40 == 39:
            time.sleep(10)
        ids = ",".join([str(nameToIds[name]) for name in nameGroup if name in nameToIds])
        movie_payload['with_'+searchType] = ids
        results = requests.get(URL+'/discover/movie', params=movie_payload).json()['results']
        count += 1
        movieDetails = []
        detail_payload = {'api_key': key, 'language': 'en-US'}
        for r in results:
            if count % 40 == 39:
                time.sleep(10)  
            if r["id"] not in movies:
                rawDetail = requests.get(URL+f"/movie/{r['id']}", params=detail_payload).json()
                # chooses only specific fields from the result and performs some corrections
                detail = onlyKeys(rawDetail, ['id', 'belongs_to_collection', 'budget', 'genres', 'release_date', 'revenue', 'runtime', 'title'])
                detail['belongs_to_collection'] = detail['belongs_to_collection'] != None
                detail['genres'] = [g['name'] for g in detail['genres']]
                movieDetails.append(detail)
                masterDetail = copy.deepcopy(detail)
                masterDetail[nameField] = copy.copy(nameGroup)
                movies[r["id"]] = rmKeys(masterDetail,["id"])
                count += 1
            else:
                # when the movie is already accounted for, skip the detailed search
                # and update the list of people associated with it
                detail = copy.deepcopy(movies[r["id"]])
                detail["id"] = r["id"]
                movieDetails.append(detail)
                for name in nameGroup:
                    if name not in movies[r["id"]][nameField]:
                        movies[r["id"]][nameField].append(name)
                    
        groupToMovies[",".join(nameGroup)] = {"ids": ids, "results": movieDetails}
        showProgress(i+1, len(nameGroups))
    log["count"] = len(movies)
    output = inp("What name should the csv and json files be saved under? Or type 'print' to see results on command line.", log) 
    if output != "print":    
        fName = output.upper()
        # Creates output folder and adds the csv file with all of the relevant detail, the json file with 
        # the groupToMovies dictionary for reference, and a log file with a summary of the program run
        if not pathlib.os.path.exists("output"):
            pathlib.Path("output").mkdir()
        if not pathlib.os.path.exists(f"output/{fName}"):
            pathlib.Path(f"output/{fName}").mkdir()
        with open(f"output/{fName}/{output}.json", "w") as f1:
            f1.write(json.dumps(groupToMovies))
        with open(f"output/{fName}/{output}.csv", "w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, fieldnames=["id", "title","release_date","budget", "revenue", nameField, "genres", "belongs_to_collection","runtime"], extrasaction="ignore")
            writer.writeheader()
            for m in movies:
                movie = movies[m]
                movie["id"] = m
                writer.writerow(movie)
        with open(f"output/{fName}/{output}.log", "w") as f2:
            p1 = "names inputted at run time" if log["inputNames"] == "manual" else log["inputNames"]
            if not len(searchGenres):
                p2 = "no search genres" 
            elif len(searchGenres) == 1:
                p2 = f"{searchGenres[0]} as a search genre"
            else:
                p2 = f"{list_representation(searchGenres)} as search genres"
            p3 = log["count"]
            f2.write(f"Application run on {p1} using {p2} with {p3} result(s)\n\n")
            f2.write("Program lines: \n")
            for line in log["lines"]:
                f2.write(line+"\n")
    else:
        essentialKeys = ["title","release_date", "revenue", nameField, "runtime"]
        movies = {i:onlyKeys(d, essentialKeys) for i,d in movies.items()}
        print(pd.DataFrame(movies).transpose())


if __name__ == "__main__":
    import sys
    main(sys.argv)