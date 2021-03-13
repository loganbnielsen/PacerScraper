# logs
import logging
logger = logging.getLogger('root')
######
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

import re

import time

class PacerDriver(webdriver.Chrome):
    def __init__(self, CONFIGS):
        options = _get_options(CONFIGS.get("run_headless"), CONFIGS.get("download_dir"))

        logger.debug("initializing driver...")
        super().__init__(CONFIGS.get("executable"), chrome_options=options)
        if CONFIGS.get("run_headless"):
            logger.debug("enabling headless download...")
            result = enable_download_in_headless_chrome(self, download_dir)
            logger.debug(f"result: {result}")
        self._require_exempt_status = CONFIGS.get('require_exempt_status')
        # value checks
        if self._require_exempt_status == None:
            raise ValueError("Must specify 'require_exempt_status' in DRIVER_CONFIGS")
        if not type(self._require_exempt_status) is bool:
            raise ValueError("'require_exempt_status' must be type bool")

    def login(self, usr, pswrd):
        isSuccess = False
        try:
            logger.debug("logging into PACER...")
            self.get("https://pacer.login.uscourts.gov/csologin/login.jsf")
            self.find_element_by_id("loginForm:loginName")\
                .send_keys(usr)
            self.find_element_by_id("loginForm:password")\
                .send_keys(pswrd)
            self.find_element_by_id("loginForm:fbtnLogin")\
                .click()
            logger.debug("loggin is successful.")
            isSuccess = True
        except Exception as e:
            logger.fatal(repr(e))
        return isSuccess

    def open_court_page(self, cname):
        isSuccess = False
        try:
            districts = WebDriverWait(self, 10).until(
                EC.presence_of_element_located((By.ID, "logoutForm:courtId_input"))
            )
            Select(districts).select_by_visible_text(cname)
            self.find_element_by_id("logoutForm:btnChangeClientCode").click()
            isSuccess = True
        except Exception as e:
            msg = repr(e)
            logger.fatal(msg)
        return isSuccess

    def open_filing_system(self):
        isSuccess= False
        WebDriverWait(self, 10).until(
                EC.presence_of_element_located((By.ID,"cmecfMainContent"))
        ).click()
        els = [el for el in self.find_elements_by_xpath("//a[@href]") if re.search("document filing system", el.text, flags=re.IGNORECASE)]
        if len(els) == 1:
            els[0].click()
            isSuccess=True
        else:
            logger.warning(f"Error finding filing system. Potential matches={len(els)}.")
        return isSuccess

    def open_query_page(self):
        isSuccess = False
        els = self.find_elements_by_xpath("//*[@id='yui-gen0']/a")
        if len(els) == 0:
            els = self.find_elements_by_xpath('//*[@id="topmenu"]/div/ul/li[1]/a')
        if len(els) == 1:
            els[0].click()
            isSuccess = True
        else:
            logger.error("Unable to find correct query button.")
        return isSuccess

    def verify_exempt(self):
        status = self.find_elements_by_xpath('//*[@id="cmecfMainContent"]/p/b')
        if len(status) != 1:
            logger.warning("Cite does not appear to support exemptions.")
        elif re.search("Exempt Court Order", status[0].text, flags=re.IGNORECASE):
            return True
        else:
            # find exemption button on query page
            els = self.find_elements_by_xpath('//*[@id="cmecfMainContent"]/p/a')
            if len(els) != 1:
                logger.warning("Cite does not appear to support exemptions.")
                return False
            else: # els == 0
                query_url = self.current_url
                # open exemption page
                els[0].click()
                # find exemption radio button and click
                WebDriverWait(self, 10).until(
                    EC.presence_of_element_located((By.ID,"exemptStatusForm:newExemptStatus:1"))
                ).click()
                # Submit
                WebDriverWait(self, 10).until(
                    EC.presence_of_element_located((By.ID,"exemptStatusForm:btnChangeToggle"))
                ).click()
                self.get(query_url)
                status = self.find_element_by_xpath('//*[@id="cmecfMainContent"]/p/b')
                if re.search("Exempt Court Order", status.text,flags=re.IGNORECASE):
                    return True
                else:
                    logger.warning("Could not toggle exemption status.")
                    return False

    def isPaywallOkay(self):
        isOkay = False
        isExempt = self.verify_exempt()
        if self._require_exempt_status == True:
            if not isExempt:
                logger.error(f"Could not turn on exemption status.")
            else:
                isOkay = True
        else:
            isOkay = True
        return isOkay

    def try_isPaywallOkay(self, page, max_atmpts=10):
        isSuccess = False
        atmpt = 0
        while not isSuccess and atmpt < max_atmpts:
            try:
                if self.isPaywallOkay():
                    isSuccess = True
                    break
                else:
                    atmpt += 1
                    self.get(page)
            except Exception as ex:
                atmpt += 1
                logger.error(f"Exception occured while checking paywall... {ex}")
        return isSuccess

    def try_case_query(self, c, max_atmpts=10):
        q_pg = self.current_url

        isSuccess = False
        atmpt = 0
        while not isSuccess and atmpt < max_atmpts:
            el_caseid = self.find_element_by_id("case_number_text_area_0")
            el_caseid.clear()
            el_caseid.send_keys(c)

            WebDriverWait(self, 10).until(
                EC.presence_of_element_located((By.ID,"case_number_find_button_0"))
            ).click()

            # TODO case handling
            res = self._get_case_text_result()
            if re.search("closed", res, re.IGNORECASE):
                el_caseid.submit()
                if self.current_url != q_pg:
                    isSuccess = True
                    break
                else:
                    atmpt += 1
            else:
                logger.error(f"Not prepared to handle case result: {res}")
                break
        return isSuccess

    def _get_case_text_result(self, max_fails = 30):
        fails = 0
        isSuccess = False
        text = ""
        while not isSuccess and fails < max_fails:
            try:
                text = WebDriverWait(self, 10).until(
                        EC.presence_of_element_located((By.ID, "case_number_message_area_0"))
                    ).text
                if re.search("looking up", text, re.IGNORECASE): # looking up case number ...
                    fails += 1
                    time.sleep(0.05)
                else:
                    isSuccess = True
            except StaleElementReferenceException as e:
                fails += 1
                time.sleep(0.05)
        return text

    def open_case_docket(self):
        # open docket sheet query page
        isSuccess = False
        els = WebDriverWait(self, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@id="cmecfMainContent"]/table/tbody/tr/td[1]/a'))
        )
        docket_links = [el for el in els if el.text == 'Docket Report ...']
        if len(docket_links) == 1:
            prev_url = self.current_url
            docket_links[0].click()
            if prev_url == self.current_url:
                url = docket_links[0].get_attribute("href")
                self.get(url)
                try:
                    WebDriverWait(self, 10).until(lambda driver: driver.current_url != prev_url) 
                except TimeoutException as ex:
                    raise Exception("Could not open Docket Report...")
        else:
            logger.fatal(f"Found inappropriate number of matches. {len(docket_links)} but expected 1")
        # verify exemption
        if self.isPaywallOkay():
            self.find_element_by_id("date_from").submit()
            isSuccess = True
        else:
            logger.fatal("Unexpectedly unable to satisfy paywall requirements.")
            isSuccess = False
        return isSuccess


### These methods should never be called from outside this file. ###

def _get_options(headless, download_dir):
    options = Options()
    options.add_argument('--no-proxy-server')
    options.add_argument('--disable-dev-shm-usage')
    if headless:
        options.add_argument('--headless')
    profile = _get_prefs(download_dir)
    options.add_experimental_option("prefs", profile)
    return options

def _get_prefs(download_dir):
     profile = {"plugins.plugins_list": [{"enabled":False,
                                          "name": "Chrome PDF Viewer"}],
                "download.default_directory": download_dir,
                "download.extensions_to_open": "",
                "profile.managed_default_content_settings.images":2,
                "profile.default_content_settin_values.automatic_downloads":1,
                "download.prompt_for_download": False,
                "plugins.always_open_pdf_externally": True
     }
     return profile