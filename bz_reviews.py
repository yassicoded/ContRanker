import csv
import argparse
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

parser = argparse.ArgumentParser()
parser.add_argument("-link")
args = parser.parse_args()

reviewList = []

class ReviewInfo:
    """
    Class for gathering Buildzoom.com main results page data (name, bz_score, link to details page,
    number of projects in each category)

    """
    def __init__(self, name, bz_score, projects, link):
        self.name = name
        self.bz_score = bz_score
        self.projects = projects
        self.link = link


def getReviews(link = 'https://www.buildzoom.com/los-angeles/general-contractors?page=1'):

    PROJECT_ROOT = os.path.abspath(os.path.dirname(''))
    DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")
    driver = webdriver.Chrome(executable_path=DRIVER_BIN)


    # WHILE NEXT BUTTON FOR MORE REVIEWS IS THERE WE WILL CONTINUE GETTING REVIEWS
    nextFound = True
    i = 1
    #while nextFound:
    for i in range(1,11):
        driver.get(link.replace("page=1",'page='+str(i)))
        print("page "+str(i))
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME,"contractor-details-header")))
        results = driver.find_elements_by_class_name('contractor-details')

        for result in results:
            theReview = ReviewInfo('', '', '', '')

            nameDiv = result.find_element_by_xpath(
                ".//div[@itemprop='name']")
            theReview.name = nameDiv.text.strip()

            try:
                scoreDiv = result.find_element_by_xpath(
                    ".//div[@class='bz-score-label']")
                theReview.bz_score =  int(scoreDiv.text.strip().split(':')[1])
            except IndexError as err:
                print("no BZ label")
                theReview.bz_score = -1

            stats = result.find_elements_by_xpath(
                ".//div[@class='project-stat-item-label']")
            stat_string = ''
            if stats is not None:
                for stat in stats:
                    stat_string += stat.text.strip() + " & "
            theReview.projects = stat_string

            details_link = result.find_element_by_class_name('contractor-name-link').get_attribute("href")
            theReview.link = details_link
            reviewList.append(theReview)




        # CHECK IF NEXT PAGE FOR MORE COMMENTS EXISTS - IF IT DOES NOT WE WILL STOP GETTING REVIEWS
        '''try:
            nextBtn = driver.find_element_by_xpath(
                "//span[@class='next']")
            nextBtn.find_element_by_tag_name('a').click()
        except NoSuchElementException:
            nextFound = False
            print("No more next found")'''

    driver.close()



def createCSV():
    """
    Save scraped data into csv file
    :return:
    """
    with open('reviews.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['name', 'bz_score', 'projects', 'link'])
        x = 1
        for review in reviewList:
            writer.writerow(
                [review.name, review.bz_score, review.projects, review.link])
            x += 1


def scrape_bz_pages():
    getReviews(args.link)
    createCSV()
