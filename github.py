import os
import io
import random
import secrets
import requests
from flask import Flask, render_template, request, Response
import getpass
import requests
import urllib.request
import time
from bs4 import BeautifulSoup
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import requests_cache
import sqlite3

#Evidence of caching results
requests_cache.install_cache('cache', backend='sqlite', expire_after=15000)

class User:
    def __init__(self):
        self.l_dates = []
        self.l_value = []
        
        self.l_dates_weeks = []
        self.l_value_weeks = []

        self.l_dates_months = []
        self.l_value_months = []

        self.score = 0
    
    def Days(self, lst1, lst2):
        self.l_dates = lst1
        self.l_value = lst2

    def Weeks(self, lst1, lst2):
        self.l_dates_weeks = lst1
        self.l_value_weeks = lst2

    def Months(self, lst1, lst2):
        self.l_dates_months = lst1
        self.l_value_months = lst2

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

text = ""
lister = []

@app.route('/plotday.png')
def plot_png():
    if (len(lister) != 0):
        output = io.BytesIO()
        FigureCanvas(lister[0]).print_png(output)
        print(lister[0].get_axes())
        # os.remove('./static/plotday.png')
        return Response(output.getvalue(), mimetype='image/png')
    else:
        print("Error!")
        return ""

@app.route('/plotweek.png')
def plot_w_png():
    if (len(lister) != 0):
        output = io.BytesIO()
        FigureCanvas(lister[1]).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')
    else:
        print("Error!")
        return ""
    
@app.route('/plotmonth.png')
def plot_m_png():
    if (len(lister) != 0):
        output = io.BytesIO()
        FigureCanvas(lister[2]).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')
    else:
        print("Error!")
        return ""

def create_figure(person, mode):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    if (mode == 1):
        # person.l_dates.reverse()
        xs = person.l_dates
        ys = person.l_value
    
    elif (mode == 2):
        # person.l_dates_weeks.reverse()
        xs = person.l_dates_weeks
        ys = person.l_value_weeks

    elif (mode == 3):
        # person.l_dates_months.reverse()
        xs = person.l_dates_months
        ys = person.l_value_months

    axis.plot(xs, ys)
    return fig

@app.route('/')
def myform():
    # global lister
    # if (len(lister) >= 3):
    #     conn = sqlite3.connect('cache.sqlite', check_same_thread=False)
    #     conn.execute("SELECT *")
    #     print(conn.fetchall())
    return render_template("name.html")

@app.route('/', methods=['POST'])
def post():
    text = request.form['user']
    user = User()
    user = GetContributionData(text, user)
    if (user == None):
        return render_template("name.html", error="user not found")

    figD = create_figure(user, 1)
    figW = create_figure(user, 2)
    figM = create_figure(user, 3)

    global lister
    if (len(lister) >= 3):
        lister = []
    lister.append(figD)
    lister.append(figW)
    lister.append(figM)

    bister = []
    bister.append(plot_png())
    bister.append(plot_w_png())
    bister.append(plot_m_png())

    return render_template("results.html", results=text, score=user.score, maji=bister)

@app.route('/launch', methods=['GET','POST'])
def launch():
    # print(text)
    return render_template("results.html", results=text)

def GetContributionData(txt, person):
    while True:
        url = "https://github.com/" + txt
        response = requests.get(url)
        if response.status_code == 404:
            print("Error! User not found. Please try again.")
            return None
        else:
            break

    response = requests.get(url)
    dateData = {}
    l_dates = []
    l_value = []

    l_dates_weeks = []
    l_value_weeks = []

    l_dates_months = []
    l_value_months = []

    week_counter = 1
    mont_counter = 1

    week_sum = 0
    mont_sum = 0
    sc = 0
    soup = BeautifulSoup(response.text, "html.parser")
    jsonData = soup.findAll('rect')
    print(jsonData)

    line_count = 0
    for tag in jsonData:
        sc += int(tag['data-count'])
        if (line_count % 7 == 0):
            l_dates_weeks.append(week_counter)
            week_counter += 1
            l_value_weeks.append(week_sum)
            week_sum = 0
        else:
            week_sum += int(tag['data-count'])

        if (line_count % 30 == 0):
            l_dates_months.append(mont_counter)
            mont_counter += 1
            l_value_months.append(mont_sum)
            mont_sum = 0
        else:
            mont_sum += int(tag['data-count'])

        l_dates.append(line_count)
        l_value.append(int(tag['data-count']))
        dateData[tag['data-date']] = tag['data-count']
        line_count += 1

    person.Days(l_dates, l_value)
    person.Weeks(l_dates_weeks, l_value_weeks)
    person.Months(l_dates_months, l_value_months)
    person.score = sc
    return person

# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

if __name__ == '__main__':
    print('starting Flask app', app.name)  
    app.run(debug=True)