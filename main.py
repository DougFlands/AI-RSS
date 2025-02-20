import threading
from app import call_api_on_start, call_api_timed, create_app
from src.core.utils.config import getEnvVariable

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
    
    app.run(debug=bool(getEnvVariable("DEBUG_MODE")))
    