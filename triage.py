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
    
# Validate tickets = checking for missing details/incomplete forms
def validate_ticket(issue):
    missing_fields = []

    description = issue.fields.description or ""

    # Check for any missing required fields in ticket, append to list of missing fields
    if "Business Justification:" not in description:
        missing_fields.append("Business Justification")

    if "Technical Parameters:" not in description:
        missing_fields.append("Technical Parameters (e.g., IP addresses, domains)")

    # return list of missing fields
    return missing_fields

# Append comment and tag author of incomplete ticket and transition ticket status
def notify_author_and_transition(jira_client, issue, missing_fields):
    transition_id = os.getenv('TRANSITION_ID_IN_PROGRESS')
    ticket_author_id = issue.fields.reporter.accountId if issue.fields.reporter else ""
    
    # Constructing comment using Jira's tagging format
    comment_body = (
        f"Hello [~accountid:{ticket_author_id}],\n\n"
        f"Your security exception request has been marked as incomplete. "
        f"To proceed, we require the following missing information:\n"
    )

    # Add missing fields to comment body
    for field in missing_fields:
        comment_body += f"- **{field}**\n"

    comment_body += "\nPlease update this ticket at your earliest convenience :)"

    # Post comment to the ticket and transition ticket state to "In Progress".
    # In an enterprise setting, ticket state would be transitioned to a...
    #   ... custom ticket state, (e.g "Pending Information", "Pending LOB Response")... 
    #   ... ticket state.
    try:
        jira_client.add_comment(issue.key, comment_body)
        logging.info(f"Added LOB pushback comment to {issue.key}")

        if transition_id:
            jira_client.transition_issue(issue, transition_id)
            logging.info(f"Transition {issue.key} to pending state.")
        else:
            logging.warning("No transition ID found in .env. Skipping ticket status update.")

    except JIRAError as e:
        logging.error(f"Failed to process updates for {issue.key}. Reason: {e.text}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return []

if __name__ == "__main__":
    load_dotenv()
    project_key = os.getenv('JIRA_PROJECT_KEY')

    # Step 1. Authenticate to Jira
    jira_client = authenticate_jira()

    # Step 2. Fetch tickets
    unprocessed_issues = fetch_unprocessed_tickets(jira_client, project_key)

    # Step 3. Validate each fetched ticket against our required fields
    for issue in unprocessed_issues:
        logging.info(f"Processing Ticket: {issue.key} - {issue.fields.summary}")

        missing_data = validate_ticket(issue)

        # Issue warning and comment to author if ticket is found to be missing data; else, inform of successful verification
        if missing_data:
            logging.warning(f"Ticket {issue.key} is INCOMPLETE. Missing: {missing_data}")
            
            # Here is where the notification to author and transition of ticket occurs
            notify_author_and_transition(jira_client, issue, missing_data)
        else:
            logging.info(f"Ticket {issue.key} has all required info. Ready for manual review.")