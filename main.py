from fastapi import FastAPI
import secrets
import uvicorn
import pandas as pd
import random
import csv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
from pydantic import BaseModel

import time
import asyncio, requests
from multiprocessing import Pool


#  Load question database
question_bd = pd.read_csv("questions.csv")
#question_bd.to_json("questions.json", orient = "records", date_format = "epoch", double_precision = 10, force_ascii = True, date_unit = "ms", default_handler = None)

#User database 
users_db = {
  "alice": "wonderland",
  "bob": "builder",
  "clementine": "mandarine",
  "admin": "4dm1N"
}


class Question(BaseModel):
    # Class of Question : required champs to add a new question
    question_id: Optional[int]
    contenu: str
    subject : str
    use : str
    correct : str
    reponseA : str
    reponseB : str
    reponseC : str
    reponseD : Optional[str]
    remark : Optional[str]

#########################################

app = FastAPI()

#Function get_current_username: verify username & password
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    for name, password in users_db.items():    
        correct_username = secrets.compare_digest(credentials.username, name)
        correct_password = secrets.compare_digest(credentials.password, password )
        if (correct_username and correct_password): 
            return credentials.username

    
    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
            )


@app.get("/Authorization")
#Check username and password
async def read_current_user(username: str = Depends(get_current_username)):
    return {"username": username}


@app.get("/QCM")

async def get_QCM(use: str, subject: str, nb_QCM: int):
    """ Random QCM choices : 3 variables needed
    use : string, subject : string (all choices are listed in guide file)
    nb_QCM : number of QCM to show
    """
    QCM_filter = list(set(question_bd[(question_bd['use']==use) & (question_bd['subject']==subject)]['question']))
    QCM_result = []
    if len(QCM_filter) > nb_QCM:
        id_random = random.sample(range(len(QCM_filter)), nb_QCM)
    else:
        id_random = random.sample(range(len(QCM_filter)), len(QCM_filter))

    for i in id_random:
        QCM_result.append(QCM_filter[i])
    return QCM_result


@app.put("/add_question")
async def put_add_question(question: Question, credentials: HTTPBasicCredentials = Depends(security)):
    """ Verify admin login and allow admin for add new question
    """
    if credentials.username == 'admin':
        new_question = {
                'contenu': question.contenu,
                'subject': question.subject,
                'use' : question.use,
                'correct' : question.correct,
                'reponseA' : question.reponseA,
                'reponseB' : question.reponseB,
                'reponseC' : question.reponseC
                }
    with open('questions.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow(new_question)
    return new_question

#Verify point de terminaisons: Authorization & QCM
def compute_response_time_Authorization(x):
    t0 = time.time()
    requests.get(url='http://127.0.0.1:8000/Authorization')
    t1 = time.time()
    return t1 - t0


def compute_response_time_QCM(x):
    t0 = time.time()
    requests.get(url='http://127.0.0.1:8000/QCM')
    t1 = time.time()
    return t1 - t0

def overflow_requests(function, number_of_parallel_operations=10):

    with Pool(number_of_parallel_operations) as p:
        values = p.map(function, [i for i in range(
            number_of_parallel_operations)])
        s = 0
        for i in values:
            s += i
        return s/len(values)

if __name__ == '__main__':
    print("making 10 requests on the '/Authorization' endpoint ...")
    delta_t = overflow_requests(compute_response_time_Authorization, 10)
    print('took {} seconds'.format(delta_t))

    print("making 10 requests on the '/QCM' endpoint")
    delta_t = overflow_requests(compute_response_time_QCM, 10)
    print('took {} seconds'.format(delta_t))
