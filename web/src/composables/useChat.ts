import { ref, computed, watch, nextTick } from 'vue';
import { sendStreamingMCPChatMessage } from '../api/chat';
import { ChatMessage, MCPChatRequest } from '../types';

export function useChat(initialSystemPrompt = '') {
  // 消息列表
  const messages = ref<ChatMessage[]>([
    {
      content: "欢迎使用对话功能，有什么可以帮助您的？",
      role: "assistant",
      time: new Date(),
    },
  ]);

  // 输入消息
  const inputMessage = ref("");
  
  // 加载状态和错误信息
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  
  // 会话ID - 为每个MCP服务单独维护一个会话ID
  const sessionIds = ref<Record<string, string>>({});
  
  // 当前选中的MCP服务
  const selectedMcpService = ref("");
  
  // 当前会话ID
  const currentSessionId = computed(() => {
    return sessionIds.value[selectedMcpService.value] || undefined;
  });
  
  // 流式输出相关
  const currentStreamingMessage = ref<ChatMessage | null>(null);
  
  // 更新计时器
  const updateTimer = ref<number | null>(null);

  // 添加消息
  const addMessage = (message: ChatMessage) => {
    messages.value.push({
      ...message,
      time: message.time || new Date(),
    });
  };

  // 清空消息
  const clearMessages = () => {
    messages.value = [{ content: "对话已重置", role: "assistant", time: new Date() }];
  };

  // 重置会话
  const resetSession = () => {
    // 重置当前MCP服务的会话ID
    if (selectedMcpService.value) {
      delete sessionIds.value[selectedMcpService.value];
    } else {
      // 如果没有选中的MCP服务，重置所有会话ID
      sessionIds.value = {};
    }

    messages.value = [{ content: "会话已重置", role: "assistant", time: new Date() }];
    error.value = null;
  };

  // 切换MCP服务
  const switchMcpService = (serviceUrl: string) => {
    selectedMcpService.value = serviceUrl;
    // 切换服务时清空消息，但保留会话ID
    messages.value = [
      {
        content: `已切换到 ${serviceUrl ? serviceUrl : "默认"} MCP服务`,
        role: "assistant",
        time: new Date(),
      },
    ];
  };

  // 滚动到底部
  const messagesEndRef = ref<HTMLElement | null>(null);
  const scrollToBottom = () => {
    if (messagesEndRef.value) {
      messagesEndRef.value.scrollIntoView({ behavior: "smooth" });
    }
  };

  // 强制更新UI和滚动
  const updateUI = () => {
    // 清除之前的计时器
    if (updateTimer.value) {
      clearTimeout(updateTimer.value);
    }
    
    // 滚动到底部
    nextTick(() => {
      scrollToBottom();
    });

    // 设置新的计时器，更短的间隔确保更流畅的体验
    updateTimer.value = window.setTimeout(() => {
      nextTick(() => {
        scrollToBottom();
      });
      updateTimer.value = null;
    }, 30);
  };

  // 监听消息变化，自动滚动到底部
  watch(
    messages,
    () => {
      nextTick(() => {
        scrollToBottom();
      });
    },
    { deep: true }
  );

  // 发送消息
  const sendMessage = async (forceUpdate: () => void) => {
    if (!inputMessage.value.trim() || isLoading.value) return;

    // 清除之前的错误
    error.value = null;

    // 添加用户消息
    const userMessage: ChatMessage = {
      role: "user",
      content: inputMessage.value,
      time: new Date(),
    };

    messages.value.push(userMessage);

    // 清空输入框
    const messageToSend = inputMessage.value;
    inputMessage.value = "";

    // 设置加载状态
    isLoading.value = true;

    try {
      // 准备请求数据
      const requestData: MCPChatRequest = {
        message: messageToSend,
        sessionId: currentSessionId.value,
        modelType: "deepseek",
        systemPrompt: initialSystemPrompt,
        mcpUrl: selectedMcpService.value || undefined,
      };

      // 使用流式输出
      // 先创建一个空的AI回复消息
      const streamingMessage: ChatMessage = {
        content: "",
        role: "assistant",
        time: new Date(),
        has_tool_call: false,
      };

      // 添加到消息列表
      messages.value.push(streamingMessage);
      currentStreamingMessage.value = streamingMessage;

      // 发送请求，使用回调函数处理流式响应
      const { sessionId } = await sendStreamingMCPChatMessage(
        { ...requestData, createStream: true },
        (chunk: string, isComplete: boolean, hasToolCall: boolean) => {
          if (currentStreamingMessage.value) {
            // 检测工具调用
            if (hasToolCall || 
                chunk.includes("✅ 工具") || 
                chunk.includes("❌ 工具") || 
                chunk.includes("⚠️ 工具")) {
              currentStreamingMessage.value.has_tool_call = true;
            }
            
            // 更新消息内容
            if (chunk.trim()) {
              currentStreamingMessage.value.content += chunk;
              console.log("收到数据块:", chunk);
            }

            // 只有当有实际内容时才更新UI
            if (chunk.trim()) {
              updateUI();
              forceUpdate();
            }

            // 完成时更新状态
            if (isComplete) {
              console.log("流式响应完成");
              
              // 如果消息为空，从消息列表中移除
              if (!currentStreamingMessage.value.content.trim()) {
                const index = messages.value.indexOf(currentStreamingMessage.value);
                if (index !== -1) {
                  messages.value.splice(index, 1);
                }
              }

              // 清理和重置
              if (updateTimer.value) {
                clearTimeout(updateTimer.value);
                updateTimer.value = null;
              }

              // 重置加载状态
              isLoading.value = false;
              
              // 最后再强制更新一次
              updateUI();
              forceUpdate();
              currentStreamingMessage.value = null;
            }
          }
        }
      );

      // 保存会话ID
      if (sessionId) {
        sessionIds.value[selectedMcpService.value] = sessionId;
      }
    } catch (err: any) {
      console.error("发送消息失败:", err);
      error.value = err.message || "发送失败，请稍后重试";
      isLoading.value = false; // 确保错误时也重置加载状态
    }
  };

  return {
    messages,
    inputMessage,
    isLoading,
    error,
    currentStreamingMessage,
    messagesEndRef,
    selectedMcpService,
    sessionIds,
    addMessage,
    clearMessages,
    resetSession,
    switchMcpService,
    sendMessage,
    scrollToBottom
  };
} 