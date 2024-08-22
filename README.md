# Bedrock-Streamlit-Chatbot-Security
AI Hackathon Entry 

A chatbot for pentesting, compliance and vulnerability discovery

-------------
How to Set up
Prereqs:

pip install streamlit
pip install Python
pip install boto3
pip install gitlab
pip install bleach

Commands:

cd 
source my_streamlit_env/bin/activate
streamlit run appv7.py --server.port XXXX

NOTES:
First time set up only: Secrets are called using st.secrets, which requires a TOML file

mkdir -p ~/.streamlit
touch ~/.streamlit/secrets.toml
nano ~/.streamlit/secrets.toml
