"""
title: Wages Calculator 
date-created: 2022-12-13
"""
# Need to download Jinja and Flask beforehand
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename # security measure for file upload 
from pathlib import Path
import os 
import sqlite3

### VARIABLES ###
DBNAME = "wages_calculator.db"

# if replacing data, you will need to delete all database files, csv files, and txt files before rerunning
FIRSTRUN = True
if (Path.cwd()/ DBNAME).exists():
    FIRSTRUN = False

UPLOADFOLDER = 'C:/your/file/path/CSE2190-IA/Product/' # change this to your own file route 
ALLOWEDEXTENSIONS = {'csv', 'txt'}
DATAHEADINGS = []
DATACOLUMNS = []

app = Flask(__name__)
app.config['UPLOADFOLDER'] = UPLOADFOLDER

### FLASK ### 
@app.route("/", methods=["GET", "POST"])
def index():
    """
    renders the index.html file in flask, uploads files into file folder
    :return: renders file 
    """
    global FIRSTRUN, REGULARFILENAME, OVERTIMEFILENAME, PRODUCTIONFILENAME, SALESFILENAME, SUMMARYFILENAME, TOTALFILENAME
    ALERT = ""
    if request.method == 'POST': 
        # inputs # 
        REGULARFILE = request.files['inputRegularHours']
        OVERTIMEFILE = request.files['inputOvertimeFile']
        SALESFILE = request.files['inputSales']
        PRODUCTIONFILE = request.files['inputProduction']
        SUMMARYFILE = request.files['inputSummary']
        TOTALFILE = request.files['inputTotalHoursFile']
        # processing # 
        if REGULARFILE.filename == '' or OVERTIMEFILE.filename == "" or SALESFILE.filename == "" or PRODUCTIONFILE.filename == "" or SUMMARYFILE.filename == "" or TOTALFILE.filename == "":
            ALERT = "Please select all files!"
        if REGULARFILE and allowed_file(REGULARFILE.filename) and OVERTIMEFILE and allowed_file(OVERTIMEFILE.filename) and SALESFILE and allowed_file(SALESFILE.filename) and PRODUCTIONFILE and allowed_file(PRODUCTIONFILE.filename) and SUMMARYFILE and allowed_file(SUMMARYFILE.filename) and TOTALFILE and allowed_file(TOTALFILE.filename):
            
            # checks if all files have been selected and uploads files 
            REGULARFILENAME = secure_filename(REGULARFILE.filename)
            REGULARFILE.save(os.path.join(app.config['UPLOADFOLDER'], REGULARFILENAME))

            OVERTIMEFILENAME = secure_filename(OVERTIMEFILE.filename)
            OVERTIMEFILE.save(os.path.join(app.config['UPLOADFOLDER'], OVERTIMEFILENAME))

            SALESFILENAME = secure_filename(SALESFILE.filename)
            SALESFILE.save(os.path.join(app.config['UPLOADFOLDER'], SALESFILENAME))

            PRODUCTIONFILENAME = secure_filename(PRODUCTIONFILE.filename)
            PRODUCTIONFILE.save(os.path.join(app.config['UPLOADFOLDER'], PRODUCTIONFILENAME))

            SUMMARYFILENAME = secure_filename(SUMMARYFILE.filename)
            SUMMARYFILE.save(os.path.join(app.config['UPLOADFOLDER'], SUMMARYFILENAME))

            TOTALFILENAME = secure_filename(TOTALFILE.filename)
            TOTALFILE.save(os.path.join(app.config['UPLOADFOLDER'], TOTALFILENAME))
            # outputs # 
            ALERT = "All files have been uploaded!"
            if FIRSTRUN:
                print((app.config['UPLOADFOLDER'], REGULARFILENAME))
                REGULARDATA, OVERTIMEDATA, SUMMARYDATA, TOTALDATA, PRODUCTIONDATA, SALESDATA = extractFiles(REGULARFILENAME, TOTALFILENAME, OVERTIMEFILENAME, SUMMARYFILENAME, PRODUCTIONFILENAME, SALESFILENAME)
                setupDatabase(REGULARDATA, OVERTIMEDATA, SUMMARYDATA, TOTALDATA, PRODUCTIONDATA, SALESDATA)
                TOTALWAGES = calculateWages()
                wageDatabase(TOTALWAGES)
                global DATAHEADINGS, DATACOLUMNS
                DATAHEADINGS, DATACOLUMNS = getMemberData(REGULARDATA, OVERTIMEDATA, PRODUCTIONDATA, SALESDATA, TOTALWAGES)
                FIRSTRUN = False
    return render_template("index.html", alert=ALERT)

@app.route("/data.html", methods=["GET", "POST"])
def data():
    """
    renders the data.html file in flask 
    :return: renders file 
    """
    global DATAHEADINGS, DATACOLUMNS
    ALERT = ""
    if DATAHEADINGS == [] or DATACOLUMNS == []:
        ALERT = "Please upload files first!"
        return render_template("data.html", alert=ALERT)
    SUMMARYHEADINGS, SUMMARYCOLUMNS = getSummaryData()
    return render_template("data.html", headings=DATAHEADINGS, columns=DATACOLUMNS, alert=ALERT, summaryheadings=SUMMARYHEADINGS, summarycolumns=SUMMARYCOLUMNS)

@app.route("/member.html", methods=["GET", "POST"])
def member():
    """
    renders the member.html file in flask 
    :return: renders file 
    """
    global DATAHEADINGS, DATACOLUMNS
    ALERT = ""
    if DATAHEADINGS == [] or DATACOLUMNS == []:
        ALERT = "Please upload files first!"
        return render_template("member.html", alert=ALERT)
    elif not (DATAHEADINGS == [] or DATACOLUMNS == []) and request.form:
        MEMBERNAME = request.form.get("member_name")
        NETPROFIT = request.form.get("net_profit")
        if checkName(MEMBERNAME) and NETPROFIT == "":
            WAGE = queryWages(MEMBERNAME)
            return render_template("member.html", membername=MEMBERNAME, alert=ALERT, wage=WAGE)
        elif checkName(MEMBERNAME) and checkFloat(NETPROFIT):
            WAGE = queryWages(MEMBERNAME)
            NETPROFIT = float(NETPROFIT)
            DOLLARAMOUNT = NETPROFIT * (WAGE / 100) 
            DOLLARAMOUNT = round(DOLLARAMOUNT, 2)
            return render_template("member.html", membername=MEMBERNAME, alert=ALERT, wage=WAGE, dollars=DOLLARAMOUNT)
        else:
            ALERT = "Please input a valid name!"
    return render_template("member.html", alert=ALERT)

### FUNCTIONS ### 
def allowed_file(FILENAME):
    return '.' in FILENAME and \
           FILENAME.rsplit('.', 1)[1].lower() in ALLOWEDEXTENSIONS # splits the filename at the . and checks if it can be used

def checkFloat(VALUE) -> bool:
    """
    checks if a string contains a float 
    :param VALUE: str
    :return: bool
    """
    try:
        float(VALUE)
        return True
    except ValueError:
        return False

def checkName(NAME) -> bool:
    """
    checks if the name is in the database
    :param NAME: str
    :return: bool
    """
    CONNECTION = sqlite3.connect(DBNAME)
    CURSOR = CONNECTION.cursor()

    try:
        CURSOR.execute(f"""
            SELECT
                percent_wages
            FROM
                wages
            WHERE
                member_name = ?;
        """, [NAME]).fetchone()
        return True
    except TypeError:
        return False

def checkTitle(TITLE):
    """
    checks titles for sqlite injection attacks 
    :param TITLE: str 
    :return: str 
    """
    while ";" in TITLE:
        TITLE = TITLE.replace(';', '')
    return TITLE

### SQLITE ###

# INPUTS # 
def extractFiles(REGULARFILENAME, TOTALFILENAME, OVERTIMEFILENAME, SUMMARYFILENAME, PRODUCTIONFILENAME, SALESFILENAME) -> list:
    """
    reads files and extracts data from csv files
    :param REGULARFILENAME: str
    :param TOTALFILENAME: str
    :param OVERTIMEFILENAME: str
    :param SUMMARYFILENAME: str
    :param PRODUCTIONFILENAME: str
    :param SALESFILENAME: str
    :return: REGULARDATA list, OVERTIMEDATA list, SUMMARYDATA list, TOTALDATA list, PRODUCTIONDATA list, SALESDATA list
    """

    REGULARFILENAME = open(os.path.join(app.config['UPLOADFOLDER'], REGULARFILENAME))
    REGULARDATA = REGULARFILENAME.readlines()
    SUMMARYFILENAME = open(os.path.join(app.config['UPLOADFOLDER'], SUMMARYFILENAME))
    SUMMARYDATA = SUMMARYFILENAME.readlines()
    OVERTIMEFILENAME = open(os.path.join(app.config['UPLOADFOLDER'], OVERTIMEFILENAME))
    OVERTIMEDATA = OVERTIMEFILENAME.readlines()
    TOTALFILENAME = open(os.path.join(app.config['UPLOADFOLDER'], TOTALFILENAME))
    TOTALDATA = TOTALFILENAME.readlines()
    PRODUCTIONFILENAME = open(os.path.join(app.config['UPLOADFOLDER'], PRODUCTIONFILENAME))
    PRODUCTIONDATA = PRODUCTIONFILENAME.readlines()
    SALESFILENAME = open(os.path.join(app.config['UPLOADFOLDER'], SALESFILENAME))
    SALESDATA = SALESFILENAME.readlines()

    # REGULAR HOURS DATA 
    for i in range(len(REGULARDATA)):
        if REGULARDATA[i][-1] == "\n":
                REGULARDATA[i] = REGULARDATA[i][:-1] 
        REGULARDATA[i] = REGULARDATA[i].split(",")
        for j in range(len(REGULARDATA[i])):
            if checkFloat(REGULARDATA[i][j]):
                REGULARDATA[i][j] = float(REGULARDATA[i][j])

    # OVERTIME DATA 
    for i in range(len(OVERTIMEDATA)):
        if OVERTIMEDATA[i][-1] == "\n":
                OVERTIMEDATA[i] = OVERTIMEDATA[i][:-1] 
        OVERTIMEDATA[i] = OVERTIMEDATA[i].split(",")
        for j in range(len(OVERTIMEDATA[i])):
            if OVERTIMEDATA[i][j] == '':
                OVERTIMEDATA[i][j] = 0
            if checkFloat(OVERTIMEDATA[i][j]):
                OVERTIMEDATA[i][j] = float(OVERTIMEDATA[i][j])
    
    # SUMMARY DATA
    for i in range(len(SUMMARYDATA)):
        if SUMMARYDATA[i][-1] == "\n":
                SUMMARYDATA[i] = SUMMARYDATA[i][:-1] 
        SUMMARYDATA[i] = SUMMARYDATA[i].split(",")
        for j in range(len(SUMMARYDATA[i])):
            if SUMMARYDATA[i][j].isnumeric():
                SUMMARYDATA[i][j] = int(SUMMARYDATA[i][j])
            if SUMMARYDATA[i][j] == '':
                SUMMARYDATA[i][j] = 0

    # TOTAL DATA
    for i in range(len(TOTALDATA)):
        if TOTALDATA[i][-1] == "\n":
                TOTALDATA[i] = TOTALDATA[i][:-1] 
        TOTALDATA[i] = TOTALDATA[i].split(",")
        for j in range(len(TOTALDATA[i])):
            if TOTALDATA[i][j] == '':
                TOTALDATA[i][j] = 0
            if checkFloat(TOTALDATA[i][j]):
                TOTALDATA[i][j] = float(TOTALDATA[i][j])

    # PRODUCTION DATA
    for i in range(len(PRODUCTIONDATA)):
        if PRODUCTIONDATA[i][-1] == "\n":
                PRODUCTIONDATA[i] = PRODUCTIONDATA[i][:-1] 
        PRODUCTIONDATA[i] = PRODUCTIONDATA[i].split(",")
        for j in range(len(PRODUCTIONDATA[i])):
            if PRODUCTIONDATA[i][j].isnumeric():
                PRODUCTIONDATA[i][j] = int(PRODUCTIONDATA[i][j])
            if PRODUCTIONDATA[i][j] == '':
                PRODUCTIONDATA[i][j] = 0

    # SALES DATA
    for i in range(len(SALESDATA)):
        if SALESDATA[i][-1] == "\n":
                SALESDATA[i] = SALESDATA[i][:-1] 
        SALESDATA[i] = SALESDATA[i].split(",")
        for j in range(len(SALESDATA[i])):
            if SALESDATA[i][j].isnumeric():
                SALESDATA[i][j] = int(SALESDATA[i][j])
            if SALESDATA[i][j] == '':
                SALESDATA[i][j] = 0

    return REGULARDATA, OVERTIMEDATA, SUMMARYDATA, TOTALDATA, PRODUCTIONDATA, SALESDATA

# PROCESSING # 

def setupDatabase(REGULARDATA, OVERTIMEDATA, SUMMARYDATA, TOTALDATA, PRODUCTIONDATA, SALESDATA) -> None:
    """
    creates database using data from files 
    :param REGULARDATA: list
    :param OVERTIMEDATA: list
    :param SUMMARYDATA: list
    :param TOTALDATA: list 
    :param PRODUCTIONDATA: list
    :param SALESDATA: list
    :return: None
    """
    global DBNAME
    CONNECTION = sqlite3.connect(DBNAME)
    CURSOR = CONNECTION.cursor()

    # REGULAR
    CURSOR.execute("""
            CREATE TABLE 
                regular_hours (
                    member_name TEXT NOT NULL PRIMARY KEY,
                    total_regular REAL NOT NULL
                );
        """)

    for i in range(1, len(REGULARDATA)):
        CURSOR.execute(f"""
            INSERT INTO 
                regular_hours
            VALUES (
                ?,
                ?
            );
        """, [REGULARDATA[i][0], REGULARDATA[i][-1]])

    # create multiple tables for each row of data each time
    for i in range(1, len(REGULARDATA[0])-1):
        REGULARDATA[0][i] = checkTitle(REGULARDATA[0][i])
        CURSOR.execute(f"""
            CREATE TABLE
                {REGULARDATA[0][i]} (
                    member_name TEXT NOT NULL PRIMARY KEY,
                    {REGULARDATA[0][i]} TEXT NOT NULL
                );
        """)
        for j in range(1, len(REGULARDATA)):
            CURSOR.execute(f"""
                INSERT INTO
                    {REGULARDATA[0][i]}
                VALUES (
                    ?,
                    ?
                );
            """, [REGULARDATA[j][0], REGULARDATA[j][i]])

    # OVERTIME 
    CURSOR.execute("""
            CREATE TABLE 
                overtime (
                    member_name TEXT NOT NULL PRIMARY KEY,
                    total_overtime REAL NOT NULL
                );
        """)

    for i in range(1, len(OVERTIMEDATA)):
        CURSOR.execute(f"""
            INSERT INTO 
                overtime
            VALUES (
                ?,
                ?
            );
        """, [OVERTIMEDATA[i][0], OVERTIMEDATA[i][-1]])

    # create multiple tables for each row of data each time
    for i in range(1, len(OVERTIMEDATA[0])-1):
        OVERTIMEDATA[0][i] = checkTitle(OVERTIMEDATA[0][i])
        CURSOR.execute(f"""
            CREATE TABLE
                {OVERTIMEDATA[0][i]} (
                    member_name TEXT NOT NULL PRIMARY KEY,
                    {OVERTIMEDATA[0][i]} TEXT NOT NULL
                );
        """)
        for j in range(1, len(OVERTIMEDATA)):
            CURSOR.execute(f"""
                INSERT INTO
                    {OVERTIMEDATA[0][i]}
                VALUES (
                    ?,
                    ?
                );
            """, [OVERTIMEDATA[j][0], OVERTIMEDATA[j][i]])

    # SUMMARY 
    CURSOR.execute("""
        CREATE TABLE 
            summary (
                name_of_event TEXT NOT NULL PRIMARY KEY,
                overtime INTEGER NOT NULL, 
                total_duration INTEGER NOT NULL, 
                total_attendance INTEGER NOT NULL
            );
    """) 

    for i in range(1, len(SUMMARYDATA)):
        CURSOR.execute("""
            INSERT INTO 
                summary
            VALUES (
                ?,
                ?,
                ?, 
                ?
            );
        """, [SUMMARYDATA[i][0], SUMMARYDATA[i][1], SUMMARYDATA[i][2], SUMMARYDATA[i][3]])

    # TOTAL
    CURSOR.execute("""
        CREATE TABLE
            total_hours (
                total_hours REAL NOT NULL
            );
    """)

    for i in range(1, len(TOTALDATA)):
        CURSOR.execute("""
            INSERT INTO
                total_hours
            VALUES (
                ?
            );
        """, [TOTALDATA[i][0]])

    # PRODUCTION
    CURSOR.execute("""
        CREATE TABLE
            production (
                member_name TEXT NOT NULL PRIMARY KEY,
                amount_produced INTEGER NOT NULL
            );
    """)

    for i in range(1, len(PRODUCTIONDATA)):
        CURSOR.execute("""
            INSERT INTO
                production
            VALUES (
                ?,
                ?
            );
        """, [PRODUCTIONDATA[i][0], PRODUCTIONDATA[i][1]])

    # SALES
    CURSOR.execute("""
        CREATE TABLE
            sales (
                member_name TEXT NOT NULL PRIMARY KEY,
                amount_sold INTEGER NOT NULL
            );
    """)

    for i in range(1, len(SALESDATA)):
        CURSOR.execute("""
            INSERT INTO
                sales
            VALUES (
                ?,
                ?
            );
        """, [SALESDATA[i][0], SALESDATA[i][1]])

    CURSOR.execute("""
            CREATE TABLE 
                wages (
                    member_name TEXT NOT NULL PRIMARY KEY , 
                    percent_wages REAL NOT NULL 
                );
        """)

    CONNECTION.commit()

def calculateWages() -> list:
    """
    calculates percentage wages for all members in the database 
    :return: list (each members wages in order)
    """
    global DBNAME
    CONNECTION = sqlite3.connect(DBNAME)
    CURSOR = CONNECTION.cursor()

    # fetch all data from the database 
    TOTALHOURS = CURSOR.execute("""
        SELECT
            *
        FROM
            total_hours;
    """).fetchone()

    MEMBERREGULAR = CURSOR.execute("""
        SELECT
            *
        FROM 
            regular_hours;
    """).fetchall()

    MEMBEROVERTIME = CURSOR.execute("""
        SELECT 
            * 
        FROM    
            overtime;
    """).fetchall()

    MEMBERPRODUCTION = CURSOR.execute("""
        SELECT
            *
        FROM
            production;
    """).fetchall()

    MEMBERSALES = CURSOR.execute("""
        SELECT
            *
        FROM
            sales; 
    """).fetchall()

    # calculate total hours 
    TOTALHOURS = TOTALHOURS[0]

    # calculate each members percentage 
    TOTALWAGES = []
    TOTALPERCENTAGE = 100

    for i in range(len(MEMBERREGULAR)): # the length of MEMBERREGULAR should be the same as the other lists 
        # distributes all wages based solely on hours 
        TOTALMEMBER = MEMBERREGULAR[i][1] + MEMBEROVERTIME[i][1]
        MEMBERWAGES = TOTALMEMBER/TOTALHOURS * 100
        # calculates regular hours 
        MEMBERREGULAR[i] = list(MEMBERREGULAR[i])
        while MEMBERREGULAR[i][1] >= 20:
            TOTALMEMBER = TOTALMEMBER * 1.02
            MEMBERWAGES = TOTALMEMBER/TOTALHOURS * 100
            MEMBERREGULAR[i][1] = MEMBERREGULAR[i][1] - 20
        # calculates production 
        MEMBERPRODUCTION[i] = list(MEMBERPRODUCTION[i])
        while MEMBERPRODUCTION[i][1] >= 20:
            TOTALMEMBER = TOTALMEMBER * 1.02
            MEMBERWAGES = TOTALMEMBER/TOTALHOURS * 100
            MEMBERPRODUCTION[i][1] = MEMBERPRODUCTION[i][1] - 20
        # calculates sales 
        MEMBERSALES[i] = list(MEMBERSALES[i])
        while MEMBERSALES[i][1] >= 20:
            TOTALMEMBER = TOTALMEMBER * 1.02
            MEMBERWAGES = TOTALMEMBER/TOTALHOURS * 100
            MEMBERSALES[i][1] = MEMBERSALES[i][1] - 20
        # calculates overtime hours 
        MEMBEROVERTIME[i] = list(MEMBEROVERTIME[i])
        while MEMBEROVERTIME[i][1] >= 20:
            TOTALMEMBER = TOTALMEMBER * 1.05
            MEMBERWAGES = TOTALMEMBER/TOTALHOURS * 100
            MEMBEROVERTIME[i][1] = MEMBEROVERTIME[i][1] - 20
        TOTALPERCENTAGE = TOTALPERCENTAGE - MEMBERWAGES
        TOTALWAGES.append(MEMBERWAGES)
    
    # distributes any overcompensations equally 
    if TOTALPERCENTAGE != 0:
        for i in range(len(TOTALWAGES)):
            PERCENTAGE = TOTALPERCENTAGE / len(TOTALWAGES)
            TOTALWAGES[i] = TOTALWAGES[i] + PERCENTAGE

    for i in range(len(TOTALWAGES)):
        TOTALWAGES[i] = round(TOTALWAGES[i], 2)
    return TOTALWAGES

def wageDatabase(TOTALWAGES) -> None:
    """
    creates a database with wage information 
    :return: None
    """
    global DBNAME
    CONNECTION = sqlite3.connect(DBNAME)
    CURSOR = CONNECTION.cursor()

    MEMBERREGULAR = CURSOR.execute("""
        SELECT
            member_name
        FROM 
            regular_hours;
    """).fetchall()

    for i in range(len(TOTALWAGES)):
        CURSOR.execute("""
            INSERT INTO 
                wages
            VALUES (
                ?,
                ?
            );
        """, [MEMBERREGULAR[i][0], TOTALWAGES[i]])

    CONNECTION.commit()

def getMemberData(REGULARDATA, OVERTIMEDATA, PRODUCTIONDATA, SALESDATA, TOTALWAGES) -> list:
    """
    organizes data into one list for easy viewing
    :param REGULARDATA: list
    :param OVERTIMEDATA: list
    :param SUMMARYDATA: list
    :param TOTALDATA: list 
    :param PRODUCTIONDATA: list
    :param SALESDATA: list
    :param TOTALWAGES: list
    :return: HEADINGS list, COLUMNS list
    """
    HEADINGS = []
    COLUMNS = []
    
    # first, let's make the headings 
    for i in range(len(REGULARDATA[0])):
        HEADINGS.append(REGULARDATA[0][i])
    
    for i in range(1, len(OVERTIMEDATA[0])):
        HEADINGS.append(OVERTIMEDATA[0][i])

    for i in range(1, len(PRODUCTIONDATA[0])):
        HEADINGS.append(PRODUCTIONDATA[0][i])
    
    for i in range(1, len(SALESDATA[0])):
        HEADINGS.append(SALESDATA[0][i])
    
    HEADINGS.append("Percent Wages")

    # add data that is in each column 

    for i in range(1, len(REGULARDATA)):
        COLUMNS.append(REGULARDATA[i])
    
    for i in range(1, len(OVERTIMEDATA)):
        for j in range(1, len(OVERTIMEDATA[i])):
            COLUMNS[i-1].append(OVERTIMEDATA[i][j])
    
    for i in range(1, len(PRODUCTIONDATA)):
        for j in range(1, len(PRODUCTIONDATA[i])):
            COLUMNS[i-1].append(PRODUCTIONDATA[i][j])

    for i in range(1, len(SALESDATA)):
        for j in range(1, len(SALESDATA[i])):
            COLUMNS[i-1].append(SALESDATA[i][j])
    
    for i in range(len(TOTALWAGES)):
        COLUMNS[i].append(TOTALWAGES[i])

    return HEADINGS, COLUMNS

def queryWages(NAME) -> None:
    """
    queries the wages table for a members wages
    :param NAME: str
    :return: None
    """
    CONNECTION = sqlite3.connect(DBNAME)
    CURSOR = CONNECTION.cursor()
    
    WAGE = CURSOR.execute(f"""
        SELECT
            percent_wages
        FROM
            wages
        WHERE
            member_name = "{NAME}";
    """).fetchone()

    return WAGE[0]

def getSummaryData() -> list: 
    """
    queries database for summary data and organizes it so it can be printed into a table
    :return: list 
    """
    global DBNAME
    CONNECTION = sqlite3.connect(DBNAME)
    CURSOR = CONNECTION.cursor()
    SUMMARYDATA = CURSOR.execute("""
        SELECT 
            * 
        FROM
            summary
    """).fetchall()

    HEADINGS = ["Name of Event", "Overtime", "Total Duration", "Total Attendance"]

    return HEADINGS, SUMMARYDATA

### MAIN PROGRAM CODE ### 
if __name__ == "__main__":
    app.run(debug=True)