from src.core.utils.config import getEnvVariable

MAIL_SERVER = getEnvVariable("MAIL_SERVER")  
MAIL_PORT = getEnvVariable("MAIL_PORT")  
MAIL_USE_TLS = True  
MAIL_USE_SSL = False 
MAIL_USERNAME = getEnvVariable("MAIL_USERNAME")  
MAIL_PASSWORD = getEnvVariable("MAIL_PASSWORD") 
# MAIL_DEFAULT_SENDER = 'your_email@example.com' 
