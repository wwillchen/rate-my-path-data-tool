import pymongo
import dotenv
import json
from bs4 import BeautifulSoup
import requests
import os


dotenv.load_dotenv()
mongo = pymongo.MongoClient(os.getenv("MONGO_URL"))
course_order_attrs = ["intellectually_stimulating", "course_rating", "instructor_score", "difficulty", "hours"]

with open("approved_subjects.txt", "r") as file:
    subjs = file.readlines()




termid = 8526

# while True:
headers={
    "Content-Type": "application/json; charset=utf-8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Host": "duke.evaluationkit.com",
    "Pragma": "no-cache",
    "Referer": "https://duke.evaluationkit.com/Report/Public",
    "ec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "Cookie": os.getenv("DUKE_COOKIE"),
}
db = mongo.rate_my_path
collection = db.ratings

for subj in subjs:
    codes = subj.split(" - ")
    code = codes[0]
    page = 1
    course_access_d = {}
    processed = []
    all_data = []
    while True:
        r = requests.get(f"https://duke.evaluationkit.com/AppApi/Report/PublicReport?Course={code}&Instructor=&TermId={termid}&Year=&AreaId=&QuestionKey=&Search=true&page={page}", headers=headers)
        js = r.json()
        has_more = bool(js["hasMore"])
        for itm in js["results"]:
            md = {}
            md["term"] = termid
            md["subj_code"] = code
            soup = BeautifulSoup(itm, features="html.parser")
            cod = soup.find("p", {"class": "sr-dataitem-info-code"}).text.split("-")
            if not cod[2].startswith("001"):
                if cod[2].startswith("01") and (cod[2].strip().lower().endswith("d") or cod[2].strip().lower().endswith("l")):
                    continue
            md["code"] = cod[1]
            md["specific_code"] = f"{cod[1]}-{cod[2]}".strip()
            inst = soup.find("p", {"class": "sr-dataitem-info-instr"}).text.split(",")
            instructor = " ".join([i for i in inst[::-1]]).strip()
            if cod[1] in processed:
                for elm in all_data:
                    if elm["code"] == cod[1]:
                        print(elm)
                        elm["instructor"].append(instructor)
                continue
            else:
                md["instructor"] = [instructor]
            processed.append(cod[1])
            uuid = soup.find("a", {"class": "accordion-toggle collapsed getQuestions"})["data-uid"]
            codes = requests.get(f"https://duke.evaluationkit.com/AppApi/Report/PublicReportQuestions?UniqueKey={uuid}", headers=headers)
            if codes.status_code == 200:
                njs = codes.json()
                for o,nitm in enumerate(njs):
                    soup = BeautifulSoup(nitm, features="html.parser")
                    num = soup.find("strong").text
                    md[course_order_attrs[o]] = float(num)
            print(md)
            all_data.append(md)
        if has_more:
            page += 1
        else:
            break 
    collection.insert_many(all_data)