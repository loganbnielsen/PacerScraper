import argparse
parser = argparse.ArgumentParser()
# DEFINE ARGUMENTS
parser.add_argument("dname", help="name of the district to extract XML info from", type=str)
# LOAD ARGUMENTS
global args
args = parser.parse_args()