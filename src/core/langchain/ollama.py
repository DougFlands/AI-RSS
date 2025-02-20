from langchain_ollama import ChatOllama  # 新的导入方式
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables import RunnablePassthrough

class ChatManager:
    def __init__(self, system_prompt="", model_name="deepseek-r1:8b", ):
        # 初始化 Ollama 模型
        self.llm = ChatOllama(
            model=model_name,
            base_url="http://localhost:11434",
            system_prompt=system_prompt
        )
        
        self.memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True
        )
        
        # 系统提示词（始终保持在对话的开始）
        self.system_prompt = system_prompt
        
        # 创建提示模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # 创建对话链
        self.chain = (
            {
                "input": RunnablePassthrough(),
                "chat_history": lambda _: self.memory.load_memory_variables({})["chat_history"]
            }
            |
            self.prompt
            | self.llm
        )
    
    def chat(self, user_input: str):
        try:
            chat_history = self.memory.load_memory_variables({})["chat_history"]
            user_input = user_input + self.system_prompt
            response = self.chain.invoke({"input": user_input, "chat_history": chat_history})
            
            self.memory.save_context(
                {"input": user_input},
                {"output": response.content}
            )
            
            return response.content
            
        except Exception as e:
            return f"发生错误: {str(e)}"
    
    def reset_conversation(self):
        """重置对话历史"""
        self.memory.clear()
