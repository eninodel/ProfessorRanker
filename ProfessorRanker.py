from collections import defaultdict
from datetime import datetime
import concurrent.futures as futures
from config import username, password
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys


class ProfessorRanker:
    """This program scrapes UW's Course Evaluation Catalog for the best professors
    
    This program allows me to quickly and efficiently scrape my university's
    Course Evaluation Catalog and allows me to quickly determine which professors 
    have the highest ratings for each class I am planning to take. Based on the 
    results from this program, I then choose my courses and professors accordingly.
    """
    def __init__(self, searched_class):
        self.start = datetime.now()
        self.searched_class = searched_class
        self.username = username
        self.password = password
        self.class_links = []
        self.prof_dict_with_ratings = {}
        self.set_with_sections = set({})
        self.raw_list = []
        self.ratings_book = {}
        option = webdriver.ChromeOptions(
        )  # the following options allow selenium to run headless
        option.add_argument('log-level=3')
        option.add_argument("--silent")
        option.add_experimental_option("excludeSwitches", ["enable-logging"])
        option.add_argument('--headless')
        option.add_argument('--disable-gpu')
        option.add_argument(
            "--incognito")  # creates new instance of chrome in incognito mode
        self.browser = webdriver.Chrome(executable_path=r'chromedriver.exe',
                                        chrome_options=option)

    def main_selenium(self):
        """Main webscrapping portion that accesses the Course Evaluation Database at UW.
        """
        self.browser.get('https://www.washington.edu/cec/toc.html')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, 'weblogin_password')))
        #login portion of the scapper which allows the script access to the database
        uw_net_id_login = self.browser.find_element_by_id('weblogin_netid')
        password_login = self.browser.find_element_by_id('weblogin_password')
        uw_net_id_login.send_keys(self.username)
        password_login.send_keys(self.password)
        self.browser.find_element_by_id('submit_button').click()
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, "toolbar")))
        #This portion retrevives the section of the database where the class links will be located
        self.browser.get('https://www.washington.edu/cec/' +
                         self.searched_class[0].lower() + '-toc.html')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, "toolbar")))
        links = self.browser.find_elements_by_partial_link_text(
            self.searched_class[:3])
        #sorts all the links to find the ones relevent to the query
        for link in links:
            link = link.get_attribute("href")
            if self.searched_class.replace(" ", "") in link:
                self.class_links.append(link)

    def get_items_from_table(self, class_link):
        """Accesses the links in the class_links and stores each proffessor's ratings.
        """
        self.browser.get(class_link)
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, "toolbar")))
        proffessor = self.browser.find_element_by_xpath('//h2')
        table_data = self.browser.find_elements_by_xpath('//td')
        ratings_list = []
        ratings_dict = {}
        for data in table_data:
            text_data = data.text
            #gets the section title and the final median score
            if '%' not in text_data:
                ratings_list.append(text_data)
                #appends the section only to these data structures
                if len(text_data) > 5:
                    self.set_with_sections.add(text_data)
                    self.raw_list.append(text_data)
        #The items with even index values are the sections and the odd index items are
        #the numberical values the proffesor recieved
        for i in range(len(ratings_list)):
            if i % 2 == 0:
                ratings_dict[ratings_list[i]] = ratings_list[i + 1]
        self.prof_dict_with_ratings[proffessor.text] = ratings_dict
        # returns 1 so concurrent futures waits for each
        # subprocess to finish
        return 1

    def ranking_proffessors(self):
        """Sorts the data collected in the previous sections.

        This part fo the script looks at the data collected previously 
        and outputs the best professor(s) for each category
        """
        self.browser.close()
        for section in self.set_with_sections:
            section_counter_dict = defaultdict(list)
            for key, value in self.prof_dict_with_ratings.items():
                if section in value:
                    section_value = value[section]
                    professor = key
                    section_counter_dict[section_value].append(professor)
            sorted_numbers_list = sorted(section_counter_dict.keys())
            highest_rating = sorted_numbers_list[-1]
            profs_with_highest_score = section_counter_dict[highest_rating]
            self.ratings_book[section] = (highest_rating,
                                          profs_with_highest_score)
        print(f'Best instructors for {self.searched_class}:')
        for key, value in self.ratings_book.items():
            strin = ''
            for i in value[1]:
                strin += i
            print(key + ' ' + value[0] + ' professor(s): ' + strin)
            print('###########################')
        print('Elapsed time: ')
        print(datetime.now() - self.start)


if __name__ == '__main__':
    classs = input('Enter a class: ')
    a = ProfessorRanker(classs)
    a.main_selenium()
    with futures.ThreadPoolExecutor() as executor:
        result = executor.map(a.get_items_from_table, a.class_links)
    a.ranking_proffessors()
