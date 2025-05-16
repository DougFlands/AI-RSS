import threading
from app import call_api_on_start, call_api_timed, create_app
from src.core.utils.config import get_env_variable
import sentry_sdk

sentry_dsn = get_env_variable("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
    )

app = create_app()

print("新版本: 1.0")

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
    
    debug_mode = get_env_variable("DEBUG_MODE")
    app.run(host='0.0.0.0', debug=debug_mode and debug_mode.lower() == 'true')
    