import pymongo
import dotenv
from bs4 import BeautifulSoup
import os


dotenv.load_dotenv()
mongo = pymongo.MongoClient(os.getenv("MONGO_URL"))



def store_courses_in_db():
    subjects = []
    db = mongo.rate_my_path
    collection = db.subjects
    
    with open("colors.txt", "r") as file:
        cols = file.readlines()
    
    with open("subjects.html", 'r') as file:
        data = file.read()
        soup = BeautifulSoup(data, features='html')
        for i,itm in enumerate(soup.findAll("option")):
            
            if i >= 250 and i < 500:
                newi = i - 250
            elif i >= 500:
                newi = i - 500
            else:
                newi = i
            print(i,newi)
            subj = itm["value"]
            codes = subj.split(" - ")
            if "_" not in codes[0]:
                subjects.append(subj)
                collection.insert_one({
                "code": codes[0],
                "name": codes[1],
                "color": cols[newi].strip(),
                "enabled": False,
                })
    with open("subject_list.txt","w+") as file:
        file.write("\n".join(subjects))
    print(len(subjects))


store_courses_in_db()
