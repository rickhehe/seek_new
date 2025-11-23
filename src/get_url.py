from itertools import product
import os
from dotenv import load_dotenv
load_dotenv()


def construct_seek_url() -> str:

    WHAT = os.getenv("WHAT").split(",")
    WHERE = os.getenv("WHERE").split(",")
    SALARY_RANGE = os.getenv("SALARY_RANGE").split(",")
    DATERANGE = os.getenv("DATERANGE")

    all_combinations = list(product(WHAT, WHERE, SALARY_RANGE))
    for i in all_combinations: 
        base_url = f"https://www.seek.com.au/{i[0]}-jobs/in-{i[1]}?daterange={DATERANGE}&salaryrange={i[2]}&salarytype=annual"
        yield base_url
