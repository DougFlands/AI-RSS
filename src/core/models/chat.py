import re
import time

from src.core.langchain.ollama import ChatManager
from src.core.utils.config import getEnvVariable
from cozepy import COZE_CN_BASE_URL
from cozepy import Coze, TokenAuth, Message, ChatStatus

class AIChat:
    def __init__(self, modelType, system_prompt=""):
        self.modelType = modelType
        self.history = []
        self.system_prompt = system_prompt

    def addHistory(self, user_message, aiResponse):
        self.history.append({"user": user_message, "ai": aiResponse})

    def getResponse(self, user_input):
        if self.modelType == "ollama":
            return self._ollamaGenerate(user_input)
        elif self.modelType == "coze":
            return self._cozeGenerate(user_input)
        else:
            raise ValueError("Invalid model type")

    def _ollamaGenerate(self, user_input):
        # 直接调用模式
        # url = "http://localhost:11434/api/generate"
        # prompt = self._generatePrompt(user_input)
        # data = {
        #     "model": "deepseek-r1:8b",
        #     "prompt": prompt,
        #     "stream": False, 
        #     "options":{
        #         "temperature": 0.8, 
        #         "top_p": 0.9,
        #     }
        # }
        
        # response = requests.post(url, json=data)
        # response.raise_for_status()
        # res = response.json()
        # response = re.sub(r'<think>.*?</think>', '', res["response"], flags=re.DOTALL)
        
        # answer = {
        #     "model": res["model"],
        #     "response": response
        # }
        # return answer
        
        chat_manager = ChatManager(system_prompt=self.system_prompt)
        
        response = chat_manager.chat(user_input=user_input)
        print("AI:", response)

        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        answer = {
            "response": response
        }
        return answer


    def _cozeGenerate(self, user_input):
        
        coze = Coze(auth=TokenAuth(token=getEnvVariable("COZE_API_KEY")), base_url=COZE_CN_BASE_URL)
        bot_id = getEnvVariable("COZE_BOT_ID")
        user_id = getEnvVariable("COZE_USER_ID")

        chat_poll = coze.chat.create_and_poll(
            bot_id=bot_id,
            user_id=user_id,
            additional_messages=[
                Message.build_user_question_text(content=user_input+self.system_prompt),
            ],
        )   

        max_wait_time = 600 
        poll_interval = 5 
        start_time = time.time()
        is_error = None

        while True:
            if chat_poll.chat.status == ChatStatus.COMPLETED:
                break  
            elif chat_poll.chat.status == ChatStatus.FAILED:
                is_error="Coze API Error: Chat failed."
                break 
            elif time.time() - start_time > max_wait_time:
                is_error="Coze API Error: Timeout waiting for response."
                break 
            time.sleep(poll_interval)
        if is_error:
            return is_error

        full_response = ""
        for message in chat_poll.messages:
            full_response += message.content
            
        parts = re.split(r'\{', full_response, maxsplit=1)
        if len(parts) >= 1:
            full_response = parts[0]
            full_response = full_response.replace("\n", "")
            
        answer = {
            "model": "coze", 
            "response": full_response,
        }

        return answer
    
    def _generatePrompt(self, user_input):
        context = ["你是一个聊天机器人，正在与一个用户进行对话。"]
        for item in self.history:
            context.append(f"用户问: {item['user']}")
            context.append(f"你答: {item['ai']}")
        context.append(f"用户问: {user_input}")
        return "\n".join(context)