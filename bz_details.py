import argparse
import pandas as pd
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

parser = argparse.ArgumentParser()
parser.add_argument("-link")
args = parser.parse_args()
reviewList = []



def getDetails(contractor_link):
    """
    scrape details of each contractor's page

    :param contractorLink: contractor's page link
    :return: scraped details of contractors page (reviews, price count, insurance, etc.)
    """

    PROJECT_ROOT = os.path.abspath(os.path.dirname(''))
    DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")
    driver = webdriver.Chrome(executable_path=DRIVER_BIN)

    driver.get(contractor_link)
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "bz-info-table")))

    tables = driver.find_elements_by_class_name("bz-info-table")
    details = {}

    for table in tables:
        rows = table.find_elements_by_tag_name('tr')
        for row in rows:
            cols = row.find_elements_by_tag_name('td')
            cols = [ele.text.strip() for ele in cols]
            details[cols[0]]=cols[1]

    try:
        numb_permits = driver.find_elements_by_class_name("badge-text-value")
        if len(numb_permits)>1:
            details['numb_permits']=numb_permits[1].text.strip()
    except NoSuchElementException:
            details['numb_permits'] = 0


    try:
        numb_revs = driver.find_element_by_class_name("contractor-rating-review-count")
        if numb_revs is not None:
            details['numb_revs'] = int(numb_revs.text.strip())

        rate = driver.find_element_by_xpath("//meta[@itemprop='ratingValue']")
        if rate is not None:
            details['rate'] = float(rate.get_attribute("content"))
    except NoSuchElementException:
        print("no review")
        details['rate'] =-1
        details['numb_revs'] = 0

    '''driver.execute_script("window.scrollTo(0, 2000)")
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "bar-graph-fill-text")))
    '''
    try :
        element = driver.find_element_by_class_name("key-stats-activity")
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "bar-graph-fill-text")))
    except NoSuchElementException:
        print("No historical data")


    bar_tables = driver.find_elements_by_class_name("bar-graph-set")
    i = 0
    for table in bar_tables:
        rows = table.find_elements_by_tag_name('tr')
        for row in rows:
            cols = row.find_elements_by_tag_name('td')
            bar_val = driver.find_elements_by_class_name('bar-graph-fill-text')[i].text.strip()
            bar_key = cols[1].find_element_by_xpath(".//span[@class='bar-graph-right-text']").text.strip()
            details[bar_key]=bar_val
            i+=1

    driver.close()
    return details

def scrape_bz_details():

    # with links scraped from reviews general data, dig into each contractor's page and gather more data

    contractor_links = pd.read_csv('reviews.csv',error_bad_lines=False)['link']
    details_dict = {'link': [],'License #':[],'Status':[],'Insurer':[],'Insured up to':[], 'Bonded Agent':[],'Bonded Value':[],
                    'Workers Comp Value':[],'Workers Comp':[],'numb_permits':[],'numb_revs':[], 'rate':[],
                    '2020':[], '2019':[],  '2018':[], '2017':[], '2016':[],'Home Additions':[], 'New Constructions':[],
                    'Kitchen remodels':[],'Garage Constructions':[],'< $5k':[],'$5k-$20k':[],'$20k-$50k':[],'$50k-$100k':[],
                    '$100k-$250k': [],'$250k-$500k':[],'$500k-$1mil':[],
                    }

    # chuck-based scraping to handle network issues

    for i in range (0,int(len(contractor_links)/20)+1):
        print(str(i)+"/"+str(int(len(contractor_links)/20)+1))
        for link in contractor_links[i * 20:(i + 1) * 20]:
        #for link in contractor_links[i*20:(i+1)*20]:
            details_scraped = getDetails(link)
            details_dict['link'].append(link)
            for detail in details_dict:
                if detail in details_scraped:
                    details_dict[detail].append(details_scraped[detail])
                else:
                    details_dict[detail].append(None)
        output = pd.DataFrame(details_dict)
        output.to_csv('details'+str(i)+'.csv')

    #createCSV()
