***
## 📘 Basic Overview

The Alpha Test Results Report includes everything in the Alpha Test Plan, plus the test results (i.e. pass / fail), and a reference to the User Requirements Spec (Requirements Document ID), System Requirements Spec (if applicable), and the Requirements Traceability Matrix. 

The outcome of this small web app is an Excel file output (from the exported Jira data) that includes columns for each of the fields required from the [S & G](https://www.aashtoware.org/wp-content/uploads/2022/08/SG_Notebook_09012022.pdf). 

<br>

***
## 🚀 How To Use

<br>

- Get [ngrok authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)
- Get your [Jira ApiToken](href="https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/") 
- Open [Google Colab](https://colab.research.google.com/)
- Upload the 'Templates' folder and 'Jira_Export_App.py' to your Google Colab
- Add the ngrok authtoken and the Jira ApiToken to your 'Jira_Export_App.py'
- Run the application
- At the end of it, a link will be displayed after 'Running on'

<br>

***
## ⚙️ How does it work

<br>

The application is smart enought to identify some of the common text patterns that we use on our 'Test Cases' tab, inside our Jira Ticket. The goal for this first version is to make a perfect extraction from the new template and to do it as close as possible from our tickets written prior to that template. 

- It looks for color patterns to identify whether a test passed or not
    - PASS = ![#36b37e](https://via.placeholder.com/15/36b37e/36b37e.png) `#36b37e`
    - NOT PASS = ![#bf2600](https://via.placeholder.com/15/bf2600/bf2600.png) `#bf2600`
    - NOT PASS = ![#ff5630](https://via.placeholder.com/15/ff5630/ff5630.png) `#ff5630` 
- It looks for a pattern starting with the word 'Test' and ending with a number from '0-9' to separate that part as a chunk of text considered as one distinct test case
- It looks for patterns starting with "Expected / Actual Results" and similars to identify the expected and actual results


***
## 🌱 Ecosystem

<br>


| Project               | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| [ngrok]               | cross-platform app that enables deves to expose a local server.  |
| [google-colab]        | allows anybody to W/E arbitrary python code.                     |
| [flask]               | a micro web framework.                                           |


[ngrok]: https://ngrok.com/
[google-colab]: https://colab.research.google.com/
[flask]: https://flask.palletsprojects.com/en/2.2.x/

<br>

***

## 🗒️ Improvement opportunities

- Currently the validation only occurs on the first request and should be improved
- UX / UI could be improved
- Refactoring, specially improving the regular expressions and the way the dataframe is processed
- The deployment could be changed to a more definitive path
- Improve excel file formatting
- Add new feature to implement/ remove patterns in the UI, so that we can update the "TEST CASE TEMPLATE" without needing to change the code







