import pymongo
import dotenv
from bs4 import BeautifulSoup
import requests
import os


dotenv.load_dotenv()
mongo = pymongo.MongoClient(os.getenv("MONGO_URL"))


with open("approved_subjects.txt", "r") as file:
    subjs = file.readlines()

# subject = subjs[0]

def subject_to_data(subject: str):
    db = mongo.rate_my_path
    collection = db.courses
    resp = requests.get(f"https://streamer.oit.duke.edu/curriculum/courses/subject/{subject}?access_token={os.getenv('DUKE_TOKEN')}")
    if resp.status_code == 200:
        js = resp.json()
        res = int(js["ssr_get_courses_resp"]["course_search_result"]["ssr_crs_srch_count"])
        if res < 0:
            print(f"ERROR FOR {subject}")
            return
        res = js["ssr_get_courses_resp"]["course_search_result"]["subjects"]["subject"]["course_summaries"]["course_summary"]
        # itm = res[1]
        for itm in res:
            title = itm["course_title_long"]
            crse_id = int(itm["crse_id"])
            offer_num = int(itm["crse_offer_nbr"])
            ctlg_num = itm["catalog_nbr"].strip()
            csubject = itm["subject"]
            offrd = itm["ssr_crse_typoff_cd"] or ""
            offrd_pret = itm["ssr_crse_typoff_cd_lov_descr"] or ""
            new_resp = requests.get(f"https://streamer.oit.duke.edu/curriculum/courses/crse_id/{crse_id}/crse_offer_nbr/{offer_num}?access_token={os.getenv('DUKE_TOKEN')}")
            if new_resp.status_code == 200:
                print(new_resp.url)
                data = new_resp.json()
                cdata = data["ssr_get_course_offering_resp"]["course_offering_result"]
                if int(cdata["ssr_terms_offered_count"]) >= 1:
                    ccdata = cdata["course_offering"]
                    description = ccdata["descrlong"]
                    units = float(ccdata["units_minimum"])
                    requirements = ccdata["rqrmnt_group_descr"]
                    attrs = ccdata["course_attributes"]
                    moiq = []
                    aok = []
                    if attrs:
                        aatr = attrs["course_attribute"]
                        if isinstance(aatr, list):
                            for attr in aatr:
                                if attr["crse_attr_lov_descr"] == "Curriculum-Modes of Inquiry":
                                    moiq.append(attr["crse_attr_value"])
                                elif attr["crse_attr_lov_descr"] == "Curriculum-Areas of Knowledge":
                                    aok.append(attr["crse_attr_value"])
                        elif isinstance(aatr, dict):
                            if aatr["crse_attr_lov_descr"] == "Curriculum-Modes of Inquiry":
                                moiq.append(aatr["crse_attr_value"])
                            elif aatr["crse_attr_lov_descr"] == "Curriculum-Areas of Knowledge":
                                aok.append(aatr["crse_attr_value"])
            
                    final_data = {
                        "id": crse_id,
                        "title": title,
                        "catalog": ctlg_num,
                        "subject": csubject,
                        "offered_filter": offrd,
                        "offered_pretty": offrd_pret,
                        "description": description,
                        "units": units,
                        "requirements": requirements,
                        "moiq": moiq,
                        "aok": aok
                    }
                    collection.insert_one(final_data)
                    print(final_data)
                



for subject in subjs:
    subject_to_data(subject)
