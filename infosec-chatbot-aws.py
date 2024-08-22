import boto3
import streamlit as st
import bleach
from gitlab import Gitlab

# Streamlit UI
st.image("/image-here", width=700)
st.caption(
    "Gain actionable insights to strengthen your AppSec compliance. The BOT analyzes your design, code and provides custom exploits (non-malicious)."
)
st.subheader("Infosec Chatbot", divider="rainbow")

# GitLab Configuration (using secrets.toml)
GITLAB_URL = st.secrets["gitlab"]["url"]
GITLAB_TOKEN = st.secrets["gitlab"]["token"]


def fetch_gitlab_repos(gitlab_url, private_token):
    """Fetches user-owned repositories from GitLab."""
    try:
        gl = Gitlab(gitlab_url, private_token=private_token)
        projects = gl.projects.list(owned=True)
        return [{"name": p.name, "id": p.id} for p in projects]
    except gitlab.exceptions.GitlabAuthenticationError as e:
        st.error(f"Authentication failed: {e}")
        return []


# Fetch repositories once and store in session state
if "repos" not in st.session_state:
    st.session_state.repos = fetch_gitlab_repos(GITLAB_URL, GITLAB_TOKEN)

repo_names = [repo["name"] for repo in st.session_state.repos]

# Dropdown menus
selected_repo = st.selectbox(
    "Select a GitLab repository (Optional-DEMO DROPDOWN ONLY):", repo_names
)
selected_task = st.selectbox(
    "Choose a task:",
    [
        "Review my code against company security requirements:",
        "Review my code against common vulnerabilities:",
        "Create a non-malicious pentest for this code:"
    ],
)

# Bedrock Integration
bedrock_client = boto3.client("bedrock-agent-runtime", "us-west-2")


def get_answers(task, user_code):
    # Base prompt structure
    base_prompt = f"""You are a cybersecurity engineer adept at presenting information to non-technical recipients.
    Here is the user's code:
    ```
    {user_code}
    ```
    """

    # Task-specific prompts
    task_prompts = {
        "Review my code against company security requirements:": 
            f"""{base_prompt}
            Your task is to review the code against company specific security requirements.
            - Primarily reference documents within the "company Requirements/" folder in the knowledge base.
            - If you cannot find relevant information in the "company Requirements/" folder, respond with, "No information found within the Policy or Requirements".
            - Think step by step before responding.
            - Output in bullet points, organized, and easy to read.
            """,
        "Review my code against common vulnerabilities:":
            f"""{base_prompt}
            Your task is to review the code for common security vulnerabilities, such as those outlined in the OWASP Top 10.
            - Primarily reference documents within the "Common Vulnerabilities/" folder in the knowledge base.
            - If you cannot find relevant information in the "Common Vulnerabilities/" folder, respond with, "No Issues Found".
            - Think step by step before responding.
            - Output in bullet points, organized, and easy to read.
            - Teach the developer what's wrong with the code and provide remediation suggestions.
            """,
        "Create a non-malicious pentest for this code:":
            f"""{base_prompt}
            Your task is to create a non-malicious penetration test plan for the provided code.
            - Identify potential attack vectors and vulnerabilities.
            - Suggest specific test cases to assess the code's resilience to these attacks.
            - Create a custom exploit for the user to test when possible.
            - Output in bullet points, organized, and easy to read.
            """
    }

    # Select the appropriate prompt based on the task
    prompt = task_prompts[task]

    response = bedrock_client.retrieve_and_generate(
        input={"text": prompt},
        retrieveAndGenerateConfiguration={
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": "INSERT-KB-ID-HERE",  # Replace with your actual knowledge base ID, this will contain company specific requirements and/or common vulns in an S3
                "modelArn": "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-v2",  #Make sure this is the correct model ARN
            },
            "type": "KNOWLEDGE_BASE",
        },
    )
    return response

# Chat History (using session state for persistence)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat Input and Interaction
user_code = st.text_area("Enter your code here:", height=200)

if st.button("Submit"):
    if selected_task and user_code:
        # Sanitize user input (prevent XSS attacks)
        sanitized_code = bleach.clean(user_code, tags=["br"], attributes={}, strip=True)

        # Get the response from the AI
        response = get_answers(selected_task, sanitized_code)
        
        if response:
            answer = response["output"]["text"]
            st.session_state.chat_history.append({"role": "assistant", "text": answer})

            # Display only the most recent response
            with st.chat_message("assistant"):
                st.markdown(answer)
            references = response.get('citations', [{}])[0].get('retrievedReferences', [])
            if references:
                context = references[0]['content']['text'][:200] + "..."
                doc_url = references[0]['location']['s3Location']['uri']
                st.markdown(f"<span style='color:#FFDA33'>Context used: </span>{context}", unsafe_allow_html=True)
                st.markdown(f"<span style='color:#FFDA33'>Source Document: </span>{doc_url}", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color:red'>No Context</span>", unsafe_allow_html=True)

# Reset Button
if st.button("Reset Chat"):
    st.session_state.chat_history = []
