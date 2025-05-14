import threading
from app import call_api_on_start, call_api_timed, create_app
from src.core.utils.config import get_env_variable
import sentry_sdk

sentry_sdk.init(
    dsn="https://9928242499a30e180c3e343cd5c16718@o4509322316414981.ingest.us.sentry.io/4509322318184448",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

app = create_app()

if __name__ == "__main__":
     # 创建线程
    thread1 = threading.Thread(target=call_api_timed)
    thread2 = threading.Thread(target=call_api_on_start)
    
    # 设置为守护线程
    thread1.daemon = True
    thread2.daemon = True
    
    # 启动线程
    thread1.start()
    thread2.start()
    
    app.run(host='0.0.0.0',debug=bool(get_env_variable("DEBUG_MODE")))
    