import os
from dotenv import load_dotenv
import json

load_dotenv()

def getEnvVariable(name, default=None):
    value = os.getenv(name)

    if value is None:
        if default is not None:
            value = default
        else:
            return None  

    return value

config_path = os.path.join(os.path.dirname(__file__), "../../../config.json")
with open(config_path, 'r') as file:
    data = json.load(file)
def getJsonConfig(name, default=None, ):
    if name in data:
        return data[name]
    else:
        return default

# api_key = getJsonConfig("rss_url")
# api_key = getEnvVariable("API_KEY")
