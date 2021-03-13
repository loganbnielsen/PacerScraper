# args
import arg
from arg import args
# logs
import log
import logging
logger = logging.getLogger('root')
# configs
import configs
# confidentials
import tokens
##############
import sys
import os
from os import path

# from bs4 import BeautifulSoup

import pandas as pd

from PacerDriver import PacerDriver

from tqdm import tqdm

def get_status(dname):
    df = None
    court_code = configs.DISTRICT_MAP.get(dname)
    if court_code:
        f = path.join(".metadata", court_code+".csv")
        if path.exists(f):
            # load in metadata if it exists
            df = pd.read_csv(f, parse_dates=["filingdate", "resolutiondate"])
        else:
            # create new metadata if not
            res = input(f"No meta data found for {dname}. Continue? ('y'/'n')")
            if res == "y":
                df = pd.read_excel(configs.IVERSON_FILE, parse_dates=["filingdate", "resolutiondate"])
                df['tried to pull'] = False
                df['successful pull'] = False
                df = df[df['court_code'].str.match(court_code)]
                df.to_csv(f, index=False)
            else:
                msg = f"Received '{res}'. Not continuing."
                logger.debug(msg)
                sys.exit(msg)
    else:
        raise ValueError(f"{dname} not found. Valid names are {configs.DISTRICT_MAP.keys()}")
    return df

def get_cases(dname):
    df = get_status(dname)
    df = df[df['tried to pull'] == False]
    cases = [case_num for case_num in df['caseno'] if not already_pulled(args.dname, case_num)]
    return cases

def update_status(dname, res):
    logger.debug("updating case statuses...")
    court_code = configs.DISTRICT_MAP.get(dname)
    f = path.join(".metadata", court_code+".csv")
    df = pd.read_csv(f, parse_dates=["filingdate", "resolutiondate"])
    for case_num, wasSuccess  in res:
        df.loc[df["caseno"] == case_num, ['tried to pull', 'successful pull']] = (True, wasSuccess)
    df.to_csv(f, index=False)
    logger.debug("done updating case statuses.")


def store_html(dname, case_num, html):
    save_dir = configs.HTML_SAVE_DIRECTORY.get(dname)
    if not path.exists(save_dir):
        os.makedirs(save_dir)
    _file = path.join(save_dir, case_num+".html")
    with open(_file, "w") as f:
        f.write(html)

def pull_html(driver, args, case_num):
    logger.debug("pulling html")
    isSuccess = False
    query_page = driver.current_url
    if driver.try_isPaywallOkay(query_page):
        if driver.try_case_query(case_num):
            if driver.open_case_docket():
                docket_html = driver.page_source
                store_html(args.dname, case_num, docket_html)
                isSuccess = True
    driver.get(query_page)
    logger.debug(f"finished pulling html: wasSuccess={isSuccess}")
    return isSuccess

def already_pulled(dname, case_num):
    save_dir = configs.HTML_SAVE_DIRECTORY.get(dname)
    _file = path.join(save_dir, case_num+".html")
    return path.exists(_file)

def main(args, cases):
    # start up driver
    res_tups = [] # (name, isSuccess) 
    pbar = tqdm(total=len(cases))
    driver = PacerDriver(configs.DRIVER_CONFIGS)
    if driver.login(tokens.USERNAME, tokens.PSWRD):
        if driver.open_court_page(configs.NAME_MAP.get(args.dname)):
            if driver.open_filing_system():
                if driver.open_query_page():
                    for i, case_num in enumerate(cases):
                        logger.debug(f"processing {case_num}")
                        if i % configs.SAVE_FREQ == 0:
                            update_status(args.dname, res_tups)
                            res_tups = []
                        if not already_pulled(args.dname, case_num):
                            isSuccess = pull_html(driver, args, case_num)
                        else:
                            isSuccess = True
                        res_tups.append( (case_num, isSuccess) )
                        pbar.update(1)
    pbar.close()
    update_status(args.dname, res_tups)
    driver.quit()
    

if __name__ == "__main__":
    logger.debug(f"Running script for '{args.dname}'")
    cases = get_cases(args.dname)
    if len(cases) > 0:
        main(args, cases)
    else:
        msg = "All cases have already been pulled. If this is not the case, try deleting '.metadata'."
        logger.debug(msg)
        print(msg)