# args
import arg
from arg import args
# logs
import log
import logging
logger = logging.getLogger('root')
# configurations
import configs
# beautiful soup
from bs4 import BeautifulSoup
# storage
import pandas as pd
# file management
import os
from os import path
# accessory
from itertools import chain
# progress decorator
from tqdm import tqdm

def get_htmls(dname):
    """
        dname: The district name whose htmls are to be parsed
        return: list containing the relative path for each file to be parsed
    """
    if dname == "ALL":
        htmls_parse = list(chain(
            *[get_htmls(_dname) for _dname in configs.REGISTERED_TERMINAL_KEYS]
        ))
    else:
        html_dir = configs.HTML_SAVE_DIRECTORY[dname]
        html_files = os.listdir(html_dir)
        logger.debug(f"Number of html files for {dname} is {len(html_files)}")
        docket_dir = configs.DOCKET_SAVE_DIRECTORY[dname]
        if not path.exists(docket_dir):
            os.makedirs(docket_dir)
        docket_files = [f.split(".")[-2] for f in  os.listdir(docket_dir)]
        htmls_parse = [os.path.join(html_dir,html) for html in html_files if html.split(".")[-2] not in docket_files]
        logger.debug(f"Number of files to parse for {dname} is {len(htmls_parse)}")
    return htmls_parse

def parse_dockets(dname, htmls):
    """
        dname : district to which the htmls pertain
        htmls : list of relative paths to each html file to be parsed
    """
    def parse_table_data(soup):
        """
            takes in the souped docket html page
        """
        tables = soup.find_all("table", {"border":"1", "cellpadding":"10", "cellspacing":"0"})
        assert len(tables) > 0, html
        head = False
        for table in tables:
            tbodies = table.find_all("tbody")
            for tbody in tbodies:
                rows = tbody.find_all("tr")
                assert len(rows) > 0
                if not head:
                    head, body = rows[0], rows[1:] # if head hasn't been defined yet, it's the first table which has a header
                else:
                    body = [*body, *rows] # header has already been pulled, add more rows of data
        return head, body
    def to_df(head, body):
        """
            head: soup element that are the docket header (first row of table)
            body: list of soup elements that are the rows in the body

            Note that the header and rows have not been split into cell elements yet
        """
        df = pd.DataFrame([[el.text for el in row.find_all("td")] for row in body])
        df = df.drop(1,axis=1) # 2nd column is empty (4 splits but only 0,2,3 have data)
        df.columns = [col.text for col in head.find_all("th")]
        return df

    docket_dir = configs.DOCKET_SAVE_DIRECTORY[dname]
    for html in tqdm(htmls):
        # read file into soup
        soup = BeautifulSoup(open(html).read())
        # parse needed data
        head, body = parse_table_data(soup)
        # TODO would be faster to write directly into a csv
        # compile into dataframe 
        df = to_df(head,body)
        # store as csv
        fname = html.split("/")[-1].split(".")[0]+".csv" # path/to/directory/file.html --> file.csv
        df.to_csv(path.join(docket_dir, fname), index=False)

def get_htmls_and_parse_dockets(dname):
    htmls = get_htmls(dname)
    parse_dockets(dname, htmls)

def main(dname):
    if dname == "ALL":
        for _dname in configs.REGISTERED_TERMINAL_KEYS:
            logger.debug(f"Processing htmls for '{_dname}'")
            get_htmls_and_parse_dockets(_dname)
    else:
        get_htmls_and_parse_dockets(dname)

if __name__ == "__main__":
    logger.debug(f"Running script for '{args.dname}'")
    main(args.dname)
