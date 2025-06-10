import re
import time
from typing import Literal

from src.core.langchain.ollama import ChatManager
from src.core.utils.config import get_env_variable
# from cozepy import COZE_CN_BASE_URL
# from cozepy import Coze, TokenAuth, Message, ChatStatus
from openai import OpenAI
class AIChat:
    def __init__(self, modelType: Literal["ollama", "coze", "deepseek"], system_prompt=""):
        self.modelType = modelType
        self.history = []
        self.system_prompt = system_prompt

    def add_history(self, user_message, ai_response):
        self.history.append({"user": user_message, "ai": ai_response})

    def get_response(self, user_input):
        if self.modelType == "ollama":
            return self._ollama_generate(user_input)
        # elif self.modelType == "coze":
        #     return self._coze_generate(user_input)
        elif self.modelType == "deepseek":
            return self._deepseek_generate(user_input)
        else:
            raise ValueError("Invalid model type")

    def _ollama_generate(self, user_input):
        # 直接调用模式
        # url = "http://localhost:11434/api/generate"
        # prompt = self._generate_prompt(user_input)
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

        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        answer = {
            "response": response
        }
        return answer


    # def _coze_generate(self, user_input):
        
    #     coze = Coze(auth=TokenAuth(token=get_env_variable("COZE_API_KEY")), base_url=COZE_CN_BASE_URL)
    #     bot_id = get_env_variable("COZE_BOT_ID")
    #     user_id = get_env_variable("COZE_USER_ID")

    #     chat_poll = coze.chat.create_and_poll(
    #         bot_id=bot_id,
    #         user_id=user_id,
    #         additional_messages=[
    #             Message.build_user_question_text(content=user_input+self.system_prompt),
    #         ],
    #     )   

    #     max_wait_time = 600 
    #     poll_interval = 5 
    #     start_time = time.time()
    #     is_error = None

    #     while True:
    #         if chat_poll.chat.status == ChatStatus.COMPLETED:
    #             break  
    #         elif chat_poll.chat.status == ChatStatus.FAILED:
    #             is_error="Coze API Error: Chat failed."
    #             break 
    #         elif time.time() - start_time > max_wait_time:
    #             is_error="Coze API Error: Timeout waiting for response."
    #             break 
    #         time.sleep(poll_interval)
    #     if is_error:
    #         return is_error

    #     full_response = ""
    #     for message in chat_poll.messages:
    #         full_response += message.content
            
    #     parts = re.split(r'\{', full_response, maxsplit=1)
    #     if len(parts) >= 1:
    #         full_response = parts[0]
    #         full_response = full_response.replace("\n", "")
            
    #     answer = {
    #         "model": "coze", 
    #         "response": full_response,
    #     }

    #     return answer
    
    def _deepseek_generate(self, user_input):
        client = OpenAI(api_key=get_env_variable("DEEPSEEK_KEY"), base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input},
            ],
            stream=False,
            max_tokens=4096,
            temperature=0.7
        )
        content = response.choices[0].message.content
        
        # 使用正则表达式去除开头的 ```json 和结尾的 ```
        content = re.sub(r'^```json\s*', '', content)  # 移除开头的 ```json
        content = re.sub(r'```\s*$', '', content)      # 移除结尾的 ```
            
        return content
    
    def _generate_prompt(self, user_input):
        context = ["你是一个聊天机器人，正在与一个用户进行对话。"]
        for item in self.history:
            context.append(f"用户问: {item['user']}")
            context.append(f"你答: {item['ai']}")
        context.append(f"用户问: {user_input}")
        return "\n".join(context)