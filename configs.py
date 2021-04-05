TERMINAL_KANSAS_KEY = "kansas"
TERMINAL_OHIO_NORTH_KEY = "ohio north"

REGISTERED_TERMINAL_KEYS = ["kansas", "ohio north"]


DISTRICT_MAP = {
    TERMINAL_KANSAS_KEY: "KS",
    TERMINAL_OHIO_NORTH_KEY : "OH"
}

HTML_SAVE_DIRECTORY = {
    TERMINAL_KANSAS_KEY: "kansas-html",
    TERMINAL_OHIO_NORTH_KEY: "ohio-north-html"
}

DOCKET_SAVE_DIRECTORY = {
    TERMINAL_KANSAS_KEY: "kansas-docket",
    TERMINAL_OHIO_NORTH_KEY: "ohio-north-docket"
}

NAME_MAP = {
    TERMINAL_KANSAS_KEY: "Kansas Bankruptcy Court",
    TERMINAL_OHIO_NORTH_KEY: "Ohio Northern Bankruptcy Court"
}

IVERSON_FILE = "Kansas Ohio Northern LN List.xls"

DRIVER_CONFIGS  = {
    "executable": "./chromedriver",
    "run_headless": False,
    "download_dir": ".tmp",
    "require_exempt_status": True
}

SAVE_FREQ = 20