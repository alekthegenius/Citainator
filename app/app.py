import streamlit as st
from ollama import Client
import chromadb
import requests
import bs4
import ollama
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


chrome_options = Options()

chrome_service = Service(executable_path=r"/usr/bin/chromedriver-linux64/chromedriver") 

chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--enable-javascript")
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

st.title("CitAInator")
st.subheader("Generate STOA Citations With the Power of AI")

client = Client(host="http://host.docker.internal:11434")


@st.dialog("Pulling Model")
def pull_model(model):
    st.write(f"Pulling Model: {model}, please wait a minute or two before using CitAInator")
    pulling_status = client.pull(model=model, stream=True)

    for line in pulling_status:
        st.write(line)

if "article_link" not in st.session_state:
    st.session_state.article_link = ""
if "evidence_prompt" not in st.session_state:
    st.session_state.evidence_prompt = ""
if "model" not in st.session_state:
    st.session_state.model = "mistral-nemo"
if "evidence" not in st.session_state:
    st.session_state.evidence = ""

try:
    client.chat(st.session_state.model)
except ollama.ResponseError as e:
    pull_model()
    




with st.sidebar:
    with st.form("Model Settings"):
        with st.expander("Model"):
            model =st.selectbox("Model", ("llama3:8b", "mistral-nemo"))


        setting_submit = st.form_submit_button("Update Settings")

        if setting_submit:
            try:
                client.chat(st.session_state.model)
            except ollama.ResponseError as e:
                print('Error:', e.error)
                if e.status_code == 404:
                    with st.spinner("Pulling models..."):
                        pull_model(model)
                    st.session_state.model = model

class document_complete(object):   
    def __call__(self, driver):
        script = 'return document.readyState'
        try:
            return driver.execute_script(script) == 'complete'
        except WebDriverException:
            return False

def remove_tags(html):

    # parse html content
    soup = bs4.BeautifulSoup(html, "html.parser")

    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()

    # return data by retrieving the tag content'
    return ' '.join(soup.stripped_strings)
def update_session_state(key, value):
    st.session_state[key] = st.session_state[value]

st.text_input("Enter Article Link", key="article_link_input", placeholder="https://www.cato.org/people/colin-grabow...", on_change=update_session_state("article_link", "article_link_input"))

automatic = st.checkbox("Let CitAInator choose evidence automatically from a prompt")

if automatic:
    st.text_input("Enter Evidence Prompt", value=st.session_state.evidence_prompt, placeholder="Describe what you want the evidence to be..", key="evidence_prompt_input")
else:
    st.text_input("Enter Evidence", key="evidence_input", placeholder="The evidence you want to use for the citation", value=st.session_state.evidence)

cite = st.button("Cite", use_container_width=True)

if cite:
    if st.session_state.article_link != "":

        response = requests.get(st.session_state.article_link)


        if response.status_code==200:
            st.toast("Request Successful", icon="✅")
            driver.get(st.session_state.article_link)

            WebDriverWait(driver, 10).until(document_complete())

            html = driver.page_source



            st.write(remove_tags(html))

        else:
            st.toast(f"Request Failed with Status Code: {response.status_code}", icon="❌")




        
    else:
        st.toast("Please enter an article link", icon="🔗")



