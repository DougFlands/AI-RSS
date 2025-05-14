from src.core.utils.config import get_env_variable

MAIL_SERVER = get_env_variable("MAIL_SERVER")  
MAIL_PORT = get_env_variable("MAIL_PORT")  
MAIL_USE_TLS = True  
MAIL_USE_SSL = False 
MAIL_USERNAME = get_env_variable("MAIL_USERNAME")  
MAIL_PASSWORD = get_env_variable("MAIL_PASSWORD") 
# MAIL_DEFAULT_SENDER = 'your_email@example.com' 
