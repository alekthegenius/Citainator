import streamlit as st
from ollama import Client
import chromadb
from chromadb.utils import embedding_functions
import requests
from bs4 import BeautifulSoup
import ollama
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
from htmldate import find_date
from dotenv import load_dotenv
import os
import ast

load_dotenv()


CHROMA_DATA_PATH = "chroma_data/"
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "evidence_source"


chroma_client = chromadb.Client()


embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL
)


try:
    collection = chroma_client.get_collection(name=COLLECTION_NAME)

except:
    collection = False

if collection != False:
    chroma_client.delete_collection(name=COLLECTION_NAME)

    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"},
    )
else:
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"},
    )




chrome_options = Options()

chrome_service = Service(executable_path=r"/usr/bin/chromedriver-linux64/chromedriver") 

chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--enable-javascript")
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

duck_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

st.title("CitAInator")
st.subheader("Generate STOA Citations With the Power of AI")

client = Client(host="http://host.docker.internal:11434")


language_code = 'en'
search_query = ""
number_of_results = 1
headers = {
  'Authorization': os.getenv("ACCESS_TOKEN"),
  'User-Agent': 'CitAInator (alekvasek@icloud.com)'
}

base_url = 'https://api.wikimedia.org/core/v1/wikipedia/'
endpoint = '/search/page'
wiki_url = base_url + language_code + endpoint

parameters = {'q': search_query, 'limit': number_of_results}

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
        
# Function to remove tags
def remove_tags(html):

    # parse html content
    soup = BeautifulSoup(html, "html.parser")

    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()

    # return data by retrieving the tag content
    return ' '.join(soup.stripped_strings)


def update_session_state(key, value):
    st.session_state[key] = st.session_state[value]

st.text_input("Enter Article Link", key="article_link_input", placeholder="https://www.cato.org/people/colin-grabow...")

automatic = st.checkbox("Let CitAInator choose evidence automatically from a prompt")

if automatic:
    st.text_area("Enter Evidence Prompt", value=st.session_state.evidence_prompt, placeholder="Describe what you want the evidence to be..", key="evidence_prompt_input")
else:
    st.text_area("Enter Evidence", key="evidence_input", placeholder="The evidence you want to use for the citation", value=st.session_state.evidence)

cite = st.button("Cite", use_container_width=True)

if cite:
    if st.session_state.article_link_input != "":

        response = requests.get(st.session_state.article_link_input)


        if response.status_code==200:
            st.toast("Request Successful", icon="✅")
            driver.get(st.session_state.article_link_input)

            WebDriverWait(driver, 10).until(document_complete())

            html = driver.page_source

            parsed_html = remove_tags(html)

            text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=512,
                        chunk_overlap=20,
                    )
            
            lines = text_splitter.split_text(html)
        
            st.write(lines)
            st.write(len(lines))

            for i, line in zip(range(1, len(lines)), lines):
                # Remove tags
                collection.add(
                    documents=[line],
                    ids=[f"id{i}"],
                    metadatas=[{"URL": st.session_state.article_link_input}],
                )


            
            author_chunks = collection.query(
                query_texts="Who is the author the article was written by?",
                n_results=3,
            )

            organization_name = driver.current_url

            organization_name = organization_name.replace("https://" if "https://" in organization_name else "http://","",)

            organization_name = organization_name.replace("www.", "") if "www." in organization_name else organization_name
            organization_name = organization_name.split("/")[0]
            organization_name = organization_name.split(".")[0]


            publish_date = find_date(html, original_date=True)


            last_updated_date = find_date(html, original_date=False)

            article_title = driver.title

            url = st.session_state.article_link_input

            evidence = st.session_state.evidence_input

            date_accessed = time.asctime()

            parameters = {'q': organization_name, 'limit': number_of_results}

            article_wiki = requests.get(wiki_url, headers=headers, params=parameters)

            st.write(article_wiki.json())

            article_excerpt = BeautifulSoup(article_wiki.json()["pages"][0]["excerpt"], "html.parser").get_text()

            st.write(article_excerpt)


            citation_prompt = f'''You are an AI debate citation bot. You are given this URL: {url} and the following information about the Webpage: Webpage Author(s): {author_chunks["documents"][0]}, Webpage Organization Name: {organization_name}, Webpage Publish Date: {publish_date}, Webpage Last Updated: {last_updated_date}, and Webpage Title: {article_title}. You will return back to the user a json-formmated citation with the following information:
            author(s), organization name, date_published, date_last_updated.
            Only return the json-citation. Do not include any other text. If one or more of the above information is missing, just return an empty string. Do not return any other text.'''

            ollama_output = client.generate(model=st.session_state.model, prompt=citation_prompt)
            
            st.write(f"Prompt: {citation_prompt}")

            st.write(f"Your Citation: {ollama_output["response"]}")

            author_list = list(dict(ollama_output["response"])["author(s)"])

            author_snippet = []

            for author in author_list:
                duck_driver.get(f"https://duckduckgo.com/?q={author.replace(' ', '+')}&kl=us-en")
                WebDriverWait(driver, 10).until(document_complete())

                author_snippet.append(duck_driver.find_elements(By.CLASS_NAME, ".links_deep")[0].find_element(By.CLASS_NAME, ".js-result-snippet").text)

            st.write(author_snippet)


            chroma_client.delete_collection(name=COLLECTION_NAME)

            collection = chroma_client.create_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_func,
                metadata={"hnsw:space": "cosine"},
            )


        else:
            st.toast(f"Request Failed with Status Code: {response.status_code}", icon="❌")




        
    else:
        st.toast("Please enter an article link", icon="🔗")



