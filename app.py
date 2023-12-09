from flask import Flask, render_template, redirect, url_for, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options 
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from bs4 import BeautifulSoup

meal_plan_balance = 0
days_left = 0
daily_budget = 0
app = Flask(__name__, template_folder='templates')

@app.route('/')
@app.route('/home')
def login():
    return render_template('index.html')

@app.route('/error')
def error():
    message = "Incorrect username or password"
    return render_template('index.html', message=message)

@app.route('/logged_in', methods=['POST', 'GET', 'PUT'])
def logged_in():
    global meal_plan_balance
    global days_left
    global daily_budget
    meal_plan_balance = 0
    ###########################################iables
    #Uses Flask POST and PUT commands
    #Takes username and password from login page and stores in username and password var
    if request.method == 'POST': 
        username = request.form.get('username')
        password = request.form.get('password')

    if request.method == "PUT":
        return redirect(url_for('login'))
    ############################################

    #######################################
    #Selenium opens headless incognito browser withe the url of mealplan site
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(options=options)
    browser.get('https://bing.campuscardcenter.com/ch/login.html')
    #Takes username and password gathered from Flask POST method, and sends keys to actual mealplan Binghamton site
    elem = browser.find_element(By.NAME, 'username')
    elem.send_keys(username)
    elem = browser.find_element(By.NAME, 'password')
    elem.send_keys(password + Keys.RETURN)
    #######################################
    try:      
        if browser.find_element(By.ID, 'welcome'):
            #################################
            #Beatiful Soup
            #Parses the HTML code from Selenium broswer page into soup variable, gets first name of user
            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")
            words = soup.label.text
            first_name = words.split()  
            #################################

            ###########################################################################
            #Problem: Website formats the balances in different order for different people
            #This block determines the order of the mealplan balances for the user, so it knows which balances to accumulate
            target_strings = ["Resident Holding - Carryover", "BUCS", "Meal Plan C"] 
            body_content = soup.find("body").get_text() 
            positions = {target: body_content.find(target) for target in target_strings} 
            sorted_targets = sorted(positions.keys(), key=lambda x: positions[x]) 
            ###########################################################################

            ###########################################################################
            #Reason for Code: WEbsite formats balances in different order for different people
            #Determines order of mealplan balances for the user to determine location of relevant 
            #balances in HTML code
            target_strings = ["Resident Holding - Carryover", "BUCS", "Meal Plan C"]
            body_content = soup.find("body").get_text()
            positions = {target: body_content.find(target) for target in target_strings}
            sorted_targets = sorted(positions.keys(), key=lambda x: positions[x])
            order = [sorted_targets.index(target) for target in target_strings]
            elements = soup.find_all(align="right")
            ###########################################################################

            ###########################################################################
            #Iterates through selected elements, finds element with monetary amount($), 
            #isolates the balance, and adds to meal_plan_balance
            i = 0
            for e in elements:
                e_string = str(e)
                if "$" in e_string:
                    sub1 = """<div align="right">"""
                    sub2 = "</div>"
                    idx1 = e_string.index(sub1)
                    idx2 = e_string.index(sub2)
                    result = e_string[idx1 + len(sub1) + 3: idx2]
                    if i == order[0] or i == order[2]: ##This checks to see if the balance being scanned is the one we care about
                        meal_plan_balance += float(result) #if so, add to result
                    i += 1
            ###########################################################################

            ###########################################################################
            #Calculates daily budget and days left
            #Calculated variables are passed into HTML code using Flasks render_template function
            calculate_daily_spending()
            return render_template('userPage.html', first_name = first_name[2], balance=meal_plan_balance, days=days_left, budget=daily_budget)
            ###########################################################################
    except NoSuchElementException:
        return redirect(url_for('error'))


#############################################################
#Takes meal_plan_balance that was determined from scraping HTML code with Beautiful Soup
#Calculates the daily budget and days left of semester
def calculate_daily_spending():
    global days_left
    global daily_budget
    curr_date = datetime.now() 
    if 8 <= curr_date.month <= 12:  
        end_date = datetime(curr_date.year, 12, 15)
    else:
        end_date = datetime(curr_date.year, 5, 15) 
    days_left = (end_date - curr_date).days + 1 
    daily_budget = round((meal_plan_balance / days_left), 2)
#############################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)