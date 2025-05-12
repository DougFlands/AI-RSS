import os
from dotenv import load_dotenv

load_dotenv()

def getEnvVariable(name, default=None):
    value = os.getenv(name)

    if value is None:
        if default is not None:
            value = default
        else:
            return None  

    return value
