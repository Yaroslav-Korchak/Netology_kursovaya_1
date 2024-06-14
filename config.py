import os
from dotenv import load_dotenv
load_dotenv()
os.environ["ACCESS_TOKEN"] = ""

access_token = os.getenv('ACCESS_TOKEN')

