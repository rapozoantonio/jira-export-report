"""# CONFIGURATION"""

#!pip install flask-ngrok
#!pip install flask-bootstrap
#!pip install flask_session
#!pip install pyngrok==4.1.1
#!ngrok update
#!ngrok config upgrade
#!pip install jira
#!pip install xlsxwriter
#!pip install gdown

from flask import Flask, render_template, request, session, current_app
import os
import re
import string
import numpy as np
import pandas as pd
from jira import JIRA
import base64

"""# EXPORT AND PROCESSING FUNCTIONS TO GENERATE ALPHA REPORT"""

def login_jira(email, api_token):
      server = {'server':'https://bridgeware.atlassian.net/'}
      return server, email, api_token

def load_projects(email, api_token):
      login = login_jira(email, api_token)
      jira = JIRA(login[0], basic_auth=(login[1], login[2]))
      return jira.projects()

def load_data(email, api_token, project):
  search = "project = {} AND issuetype != Epic ORDER BY key ASC".format(project) #No Epics!
  login = login_jira(email, api_token)
  jira = JIRA(login[0], basic_auth=(login[1], login[2]))

  if project == "SCDOT":
    fields = 'summary, status, components, customfield_12433, customfield_12445'
  else: #works for BRMI
    fields = 'summary, status, components, customfield_12419, customfield_12445'

  start_at = 0
  max_batch_size = 100
  issues_in_proj = jira.search_issues(search, startAt=start_at, maxResults=max_batch_size, json_result = 'true', fields = fields)
  df = pd.json_normalize(issues_in_proj["issues"], meta = fields)
  total_issues = issues_in_proj["total"]
  batches = round(total_issues/max_batch_size)
  for i in range(batches):
      start_at = max_batch_size
      max_batch_size = max_batch_size + 100 
      issues_in_proj = jira.search_issues(search, startAt=start_at, maxResults=max_batch_size, json_result = 'true', fields = fields)
      df = df.append(pd.json_normalize(issues_in_proj["issues"], meta = fields))

  if project == "SCDOT":
    fields = ["fields.status.statusCategory.name","key","fields.summary","fields.components","fields.customfield_12433.value",'fields.customfield_12445']
  else: #works for BRMI
    fields = ["fields.status.statusCategory.name","key","fields.summary","fields.components","fields.customfield_12419.value",'fields.customfield_12445']

  df = df[fields]
  new_fields = ["STATUS","TICKET","DESCRIPTION","COMPONENTS","BILLABLE_TASK","TEST_CASES"]
  df.columns = new_fields
  df["RAW_TEST_CASES"] = df["TEST_CASES"]
  status_list = df["STATUS"].unique()
  task_list = df["BILLABLE_TASK"].unique()
  
  return status_list, task_list, df

def filter_status(filtered_status, df):
  df = df[df['STATUS'].isin(filtered_status)]
  df = df.drop(['STATUS'], axis=1)
  return df

def insert_field_descriptions(df):
    final_fields = [
      "JIRA Cases / Defect #", #TICKET
      "Test Case / Procedure Description", #DESCRIPTION
      "Affected Page / Component in BrM ", #COMPONENTS
      "FDS Requirement", #BILLABLE_TASK
      "Steps", #TEST_CASES
      "RAW_TEST_CASES", #RAW_TEST_CASES
      "Test Procedure Results", #TEST_RESULTS
      "Expected Results", #EXPECTED_RESULTS
      "Actual Results" #ACTUAL_RESULTS
    ]
    df.columns = final_fields

    df.insert(0, "Requirement ID #", "")
    df.insert(3, "FDS Sub-Requirement", "")
    df.insert(8, "Test Data", "")
    df.insert(12, "Exceptions", "")
    df.insert(13, "Proposed Resolution / Action", "")

    print(df.columns)
    return df

def encode_base64(file_name):
    file_dir = os.path.join(current_app.root_path, file_name)
    data = open(file_dir, 'rb').read()
    return base64.b64encode(data).decode('UTF-8')

def remove_regex(df):
  column = "TEST_CASES"
  icon = ": " #:
  df[column] = df[column].str.replace(icon, '', regex=True)
  icon = "\(/\)" #checkmark
  df[column] = df[column].str.replace(icon, '', regex=True)
  icon = "\(!\)" #warning
  df[column] = df[column].str.replace(icon, '', regex=True)
  icon = "\(i\)" #info
  df[column] = df[column].str.replace(icon, '', regex=True)
  regex = r'{color(.*?){color}'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'!image(.*?)\!'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'#(.*?)expected'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'#(.*?)actual'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r' / '
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'expected(.*?)\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'actual(.*?)\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'expected(.*?)\.'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'actual(.*?)\.'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'\[~accountid(.*?)]'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'#####\s\s*\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'###\s\s*\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'##\s\s*\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'#\s\s*\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'\/ actual result'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  df[column] = df[column].str.strip()
  column = "EXPECTED_RESULTS"
  icon = ": " #:
  df[column] = df[column].str.replace(icon, '', regex=True)
  icon = "\(/\)" #checkmark
  df[column] = df[column].str.replace(icon, '', regex=True)
  icon = "\(!\)" #warning
  df[column] = df[column].str.replace(icon, '', regex=True)
  icon = "\(i\)" #info
  df[column] = df[column].str.replace(icon, '', regex=True)
  regex = r'{color(.*?){color}'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'!image(.*?)\!!'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'\/ actual result'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'\[~accountid(.*?)]'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'#####\s\s*\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'###\s\s*\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'##\s\s*\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  regex = r'#\s\s*\\n'
  df[column] = df[column].str.replace(regex, '', regex=True, flags = re.IGNORECASE)
  df[column] = df[column].str.strip()

  df['EXPECTED_RESULTS'] = df['EXPECTED_RESULTS'].str.replace('####','    ·')
  df['EXPECTED_RESULTS'] = df['EXPECTED_RESULTS'].str.replace('###','  ·')
  df['EXPECTED_RESULTS'] = df['EXPECTED_RESULTS'].str.replace('##',' ·')
  df['EXPECTED_RESULTS'] = df['EXPECTED_RESULTS'].str.replace('#','·')
  df['TEST_CASES'] = df['TEST_CASES'].str.replace('####','    ·')
  df['TEST_CASES'] = df['TEST_CASES'].str.replace('###','   ·')
  df['TEST_CASES'] = df['TEST_CASES'].str.replace('##','  ·')
  df['TEST_CASES'] = df['TEST_CASES'].str.replace('#','·')

  return df

def generate_alphareport(df, project, filtered_tasks, filtered_statuses):

  df["COMPONENTS"] = df["COMPONENTS"].map(lambda x:[i['name'] for i in x])
  df = filter_status(filtered_statuses, df)
  print("////////////////////////////////////////////////passing filter status")
  print("////////////////////////////////////////////////passing COMPONENTS")
  empty_test_tab = "Enter Test Case(s)"
  df.loc[df["TEST_CASES"].str.contains(empty_test_tab) == True, 'TEST_RESULTS'] = "NOT TESTED"
  df["TEST_CASES"] = df["TEST_CASES"].str.split("TEST(.*?)[0-9]").str[1:]
  df = df.explode("TEST_CASES")
  df["TEST_CASES"] = df["TEST_CASES"].str.strip()

  pass_test = "#36b37e" #MEDIUM SEA GREEN - PASS
  not_pass_test_orange = "#ff5630" #OUTRAGEOUS ORANGE - NOT PASS
  not_pass_red = "#bf2600" #HARLEY DAVIDSON ORANGE - NOT PASS
  print("////////////////////////////////////////////////passing pass test")
  
  df_regex = pd.DataFrame()
  regex = [r'actual(.*?)\{color',
          r'expected(.*?)\{color',
          r'results(.*?)\{color',
          r'actual(.*?)\\n',
          r'expected(.*?)\\n',
          r'results(.*?)\\n',
          r'actual(.*?)\.',
          r'expected(.*?)\.',
          r'results(.*?)\.']
  regex_list = []
  for regex in regex:
      regex_list.append(regex)
      df_regex[regex] = df["TEST_CASES"].str.findall(regex, flags = re.IGNORECASE).str.join(",")
      df_regex[regex] = df_regex[regex].str.replace(', ', '\n')
  
  df_regex = df_regex.replace(np.nan, '', regex=True)
  df["EXPECTED_RESULTS"] = df_regex[regex_list].apply(lambda x: max(x, key=len), axis=1)
  
  df.loc[df["TEST_CASES"].str.contains(pass_test) == True, 'TEST_RESULTS'] = "PASS"
  df.loc[df["TEST_CASES"].str.contains(not_pass_test_orange) == True, 'TEST_RESULTS'] = "NOT PASS"
  df.loc[df["TEST_CASES"].str.contains(not_pass_red) == True, 'TEST_RESULTS'] = "NOT PASS"
  print("////////////////////////////////////////////////passing regex test")
  
  df = remove_regex(df)
  print("////////////////////////////////////////////////passing cleaning")
  df["ACTUAL_RESULTS"] = df["EXPECTED_RESULTS"]

  df = df.replace(np.nan, '', regex=True)
  df = df[(df['TEST_CASES'] != '') & (df['TEST_RESULTS'] != '') & (df['EXPECTED_RESULTS'] != '') ]

  df = insert_field_descriptions(df)
  print("////////////////////////////////////////////////passing field insert")

  file_name = "{}-AlphaTestResultsReport.xlsx".format(project)
  create_excel_report(file_name, filtered_tasks, df)
  print("////////////////////////////////////////////////passing create excel report")
  
  base64_encoded = encode_base64(file_name)

  return df, base64_encoded

def create_excel_report(file_name, filtered_tasks, df):
  writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
  for filtered_task in filtered_tasks:
      print("entering loop")
      sheet_name = filtered_task[0:31].translate(str.maketrans('', '', string.punctuation)) #Remove punctuation
      df_final = df.loc[df["FDS Requirement"] == filtered_task]
      df_final.insert(0, "Test Case/Procedure ID #", np.arange(len(df_final)) + 1)
      df_final.to_excel(
          writer, 
          sheet_name=sheet_name, 
          index=False, 
          startrow=6
      )
      worksheet = writer.sheets[sheet_name]
      text_format = writer.book.add_format({'text_wrap' : True, 'valign': 'top'})
      worksheet.set_column(0,14,30, text_format)
      worksheet.write('A1', filtered_task)
      text_format = writer.book.add_format({'text_wrap' : True, 'valign': 'top', 'border' : True})
      worksheet.write('A2', 'Created By', text_format)
      worksheet.write('A3', 'Date Created', text_format)
      worksheet.write('A4', 'Functional Design Specification (FDS)', text_format)
      worksheet.write('A5', 'AASHTO Standards and Guidelines (S&G Notebook)', text_format)
      worksheet.write('C2', 'Tested By', text_format)
      worksheet.write('C3', 'Date Tested', text_format)
      worksheet.write('C4', 'Work Plan', text_format)
      worksheet.write('C5', 'JIRA/Confluence', text_format)
      cells = ['B2', 'B3', 'B4', 'B5', 'D2', 'D3', 'D4', 'D5']
      for cell in cells:
        worksheet.write(cell, '', text_format)
  return writer.save()

"""# WEB APPLICATION"""

app = Flask(__name__)

app.secret_key = os.urandom(16)

@app.route("/")
def home():
    return render_template('login.html')

@app.route("/choose-project/", methods=['POST','GET'])
def choose_project():
    session['email'] = request.form['emailAddress']
    session['api_token'] = request.form['apiToken']
    try:
      projects = load_projects(session['email'], session['api_token'])
      return render_template('choose_project.html', projects = projects)
    except:
      return render_template('login.html', warning = 'An error occurred loading the Projects! Invalid Email address or API token!')

@app.route("/choose-statuses", methods=['POST','GET'])
def choose_statuses():
    project = request.form['project']
    email = session['email']
    api_token = session['api_token']
    try:
      data = load_data(email, api_token, project)
      statuses = data[0]
      return render_template('choose_statuses.html', 
                             project = project, 
                             statuses = statuses, 
                             )
    except:
      projects = load_projects(email, api_token)
      return render_template('choose_project.html', 
                             projects = projects,
                             warning = 'An error occurred loading the Statuses! Verify if the fields on your Jira issue are different than the default for this project.'
                             )

@app.route("/choose-tasks", methods=['POST','GET'])
def choose_tasks():
    project = request.form['project']
    filtered_statuses = request.form.getlist('statuses')
    email = session['email']
    api_token = session['api_token']
    try:
      data = load_data(email, api_token, project)
      tasks = data[1]
      return render_template('choose_tasks.html', 
                             project = project, 
                             filteredStatuses = filtered_statuses, 
                             tasks = tasks
                             )
    except:
      return render_template('choose_statuses.html', 
                             project = project, 
                             filteredStatuses = filtered_statuses, 
                             warning = 'An error occurred loading the Tasks! Verify if the fields on your Jira issue are different than the default for this project.'
                             )

@app.route("/export-results", methods=['POST','GET'])
def export_results():
    project = request.form['project']
    filtered_statuses = request.form.getlist('statuses')
    filtered_tasks = request.form.getlist('tasks')
    email = session['email']
    api_token = session['api_token']
    data = load_data(email, api_token, project)
    tasks = data[1]
    df_raw = data[2]
    try:
      alpha_report = generate_alphareport(df_raw, project, filtered_tasks, filtered_statuses)
      encoded_alpha_report = alpha_report[1]
      return render_template('export_report.html',
                            project = project,
                            filteredStatuses = filtered_statuses,
                            filteredTasks = filtered_tasks,
                            encodedAlphaReport = encoded_alpha_report
                            )
    except:
      return render_template('choose_tasks.html', 
                             project = project, 
                             filteredStatuses = filtered_statuses, 
                             tasks = tasks,
                             warning = 'An error occurred generating the Report! Verify if the fields on your Jira issue are different than the default for this project.'
                             )
app.run()