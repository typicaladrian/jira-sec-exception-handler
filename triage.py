import os
import logging
from dotenv import load_dotenv
from jira import JIRA
from jira.exceptions import JIRAError

# Configure detailed logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Authenticates to Jira using basic auth (email + API key) and returns a Jira client object
def authenticate_jira():
    load_dotenv()

    server = os.getenv('JIRA_SERVER')
    email = os.getenv('JIRA_EMAIL')
    api_token = os.getenv('JIRA_API_TOKEN')

    try:
        logging.info("Attempting to connect to Jira...")
        jira_options = {'server': server}

        # Attempt to authenticate with Atlassian server
        jira = JIRA(options=jira_options, basic_auth=(email, api_token))

        logging.info(f"Successfully authenticated to Jira at {server}")
        
        # Return our successfully connected to Jira client object
        return jira
    
    except JIRAError as e:
        # Catch and log error thrown by authentication attempt
        logging.error(f"Failed to authenticate to Jira. Reason: {e.text}")
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        exit(1)

# Fetch new, unassigned tickets using JQL
# JQL (Jira Query Language) is Atlassian's version of SQL, allows us to query tickets server-side
def fetch_unprocessed_tickets(jira_client, project_key):
    # Construct our target JQL search query
    jql_query = f'project = {project_key} AND status = "To Do" ORDER BY created DESC'

    try:
        logging.info(f"Searching for tickets with JQL: {jql_query}")

        issues = jira_client.search_issues(jql_query, maxResults=50)

        logging.info(f"Successfully fetched {len(issues)} unprocessed tickets.")
        
        # Return results of JQL search query.
        #   Maximum of 50 results will be returned to prevent... 
        #       ... memory spikes in high-volume/enterprise environments
        return issues
    
    except JIRAError as e:
        logging.error(f"Failed to fetch tickets. JQL Error: {e.text}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return []
    

if __name__ == "__main__":
    load_dotenv()
    project_key = os.getenv('JIRA_PROJECT_KEY')

    # 1. Authenticate to Jira
    jira_client = authenticate_jira()

    # 2. Fetch tickets
    unprocessed_issues = fetch_unprocessed_tickets(jira_client, project_key)

    # quick testing of fetching with dummy tickets
    for issue in unprocessed_issues:
        print(f"Found Ticket: {issue.key} - {issue.fields.summary}")