#Finding movies with black actresses
import requests
import time
import json
import copy
import csv
import utils
import pathlib

def main(args):
    URL = "https://api.themoviedb.org/3"
    key = "bed5288deb39663ad0bb3a8ed2625f4a"
    nameFile = input("What file contains your list of names? (include extension)\n")
    while nameFile != "manual" and nameFile != "done":
        if not pathlib.os.path.exists(nameFile):
            nameFile = input("File not recognized. Try again or type 'manual' to enter names manually.\n").lower()
        else:
            with open(nameFile, "r") as nF:
                names = [name.strip() for name in nF.readlines()]
            nameFile = "done"
    if nameFile == "manual":
        names = []
        name = input("Type each name and then press enter. Entering names will stop when you press enter twice.\n")
        while len(name) != 0:
            names.append(name)
            name = input("")
    
    payload = {"api_key": key, "include_adult": False, "language": "en-US"}
    count = 1
    nameToIds = {}
    print("Searching TMDB for people...")
    for i, name in enumerate(names):
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
    movie_payload = {'api_key': key}
    searchType, nameField = ("crew", "crew_member") if input("Searching actors or directors?\n") == "directors" else ("cast", "actor/actress") 
    with open("genres.json", "r") as gF:
        genres = json.loads(gF.read())
    searchGenres = []
    genre = input("Any particular genre to search? Type 'done' if no.\n").lower()
    while genre != "done":
        if genre not in genres:
            genre = input("Genre not recognized. Try again or type 'done' to continue.\n").lower()
        else:
            searchGenres.append(genre)
            genre = input("Add another genre or type 'done' to continue.\n").lower()
    genreIds = ",".join([str(genres[g]) for g in searchGenres])
    movie_payload["with_genres"] = genreIds
    print("Getting movie details...")
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
    output = input("What name should the csv and json files be saved under?\n")
    time.sleep(0.8)
    if not pathlib.os.path.exists("output"):
        pathlib.Path("output").mkdir()
    with open("output/"+output+".json", "w") as f:
        f.write(json.dumps(nameToMovies))
    with open("output/"+output+".csv", "w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["id", "title","release_date","budget", "revenue", nameField, "genres", "belongs_to_collection","runtime"], extrasaction="ignore")
        writer.writeheader()
        for m in masterMovieList:
            writer.writerow(m)




if __name__ == "__main__":
    import sys
    main(sys.argv)