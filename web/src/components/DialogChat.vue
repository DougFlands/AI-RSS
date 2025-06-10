<template>
  <div class="dialog-chat">
    <el-dialog
      v-model="dialogVisible"
      :title="title"
      width="80%"
      :close-on-click-modal="false"
      :before-close="handleClose"
      class="chat-dialog"
    >
      <div class="flex flex-col h-[60vh]">
        <!-- 消息列表 -->
        <div ref="messagesContainer" class="flex-1 p-4 overflow-y-auto bg-gray-50">
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['mb-3 flex', message.role === 'user' ? 'justify-end' : '']"
          >
            <div
              :class="[
                'max-w-[70%] px-3.5 py-2.5 rounded-xl relative',
                message.role === 'user'
                  ? 'bg-blue-100 rounded-tr-sm'
                  : 'bg-white rounded-tl-sm shadow-sm',
              ]"
            >
              <div 
                class="break-words leading-relaxed markdown-body"
                v-html="formatMessageContent(message.content, message.has_tool_call)"
              ></div>
              <div class="mt-1 text-xs text-gray-500 text-right">
                {{ formatTime(message.time || new Date()) }}
              </div>
            </div>
          </div>
          
          <!-- 加载状态 -->
          <div v-if="isLoading" class="mb-3 flex">
            <div class="px-3.5 py-2.5 bg-white rounded-xl rounded-tl-sm shadow-sm">
              <div class="flex justify-center items-center h-5">
                <span
                  class="w-2 h-2 mx-0.5 bg-gray-400 rounded-full animate-bounce"
                  style="animation-delay: -0.32s"
                ></span>
                <span
                  class="w-2 h-2 mx-0.5 bg-gray-400 rounded-full animate-bounce"
                  style="animation-delay: -0.16s"
                ></span>
                <span
                  class="w-2 h-2 mx-0.5 bg-gray-400 rounded-full animate-bounce"
                ></span>
              </div>
            </div>
          </div>
          <div ref="messagesEndRef"></div>
        </div>

        <!-- 输入框 -->
        <div class="p-4 bg-white border-t border-gray-200">
          <div class="flex">
            <el-input
              v-model="inputMessage"
              placeholder="请输入消息..."
              @keydown="handleKeyDown"
              :disabled="isLoading"
              type="textarea"
            ></el-input>
            <el-button
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading"
              :class="{'opacity-75': isLoading}"
              type="primary"
              class="ml-2"
              style="height: 52px"
            >
              <span v-if="isLoading">发送中...</span>
              <span v-else>发送</span>
            </el-button>
          </div>
          <div v-if="error" class="mt-2 p-2 bg-red-50 text-red-600 text-sm rounded-md">
            {{ error }}
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, defineProps, defineEmits, defineExpose, onMounted } from "vue";
import { sendMCPChatMessage } from "../api/chat";
import { ChatMessage, MCPChatRequest } from "../types";
import { marked } from 'marked';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: "对话"
  },
  initialSystemPrompt: {
    type: String,
    default: ""
  },
});

const emit = defineEmits(["update:visible", "close", "send"]);

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value)
});

// 消息列表
const messages = ref<ChatMessage[]>([
  {
    content: "欢迎使用对话功能，有什么可以帮助您的？",
    role: "assistant",
    time: new Date()
  }
]);

// 输入消息
const inputMessage = ref("");
const messagesContainer = ref<HTMLElement | null>(null);
const messagesEndRef = ref<HTMLElement | null>(null);

// 加载状态和错误信息
const isLoading = ref(false);
const error = ref<string | null>(null);

// 会话ID
const sessionId = ref<string | undefined>(undefined);

// 配置 marked 选项
onMounted(() => {
  marked.setOptions({
    breaks: true,        // 支持换行符转换为 <br>
    gfm: true,           // 启用 GitHub 风格的 Markdown
  });
});

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

// 格式化时间
const formatTime = (time: Date) => {
  return `${time.getHours().toString().padStart(2, "0")}:${time
    .getMinutes()
    .toString()
    .padStart(2, "0")}`;
};

// 滚动到底部
const scrollToBottom = () => {
  if (messagesEndRef.value) {
    messagesEndRef.value.scrollIntoView({ behavior: "smooth" });
  }
};

// 格式化消息内容，处理MCP工具调用结果和Markdown
const formatMessageContent = (content: string, has_tool_call?: boolean) => {
  let processedContent = content;
  
  // 处理工具调用结果
  if (has_tool_call) {
    processedContent = content.replace(
      /(✅|❌|⚠️) 工具 '(.+?)' (调用结果|调用失败|不可用).*?```([\s\S]*?)```/g,
      (match, status, toolName, result, toolOutput) => {
        let className = '';
        if (status === '✅') className = 'bg-green-50 border-green-200';
        if (status === '❌') className = 'bg-red-50 border-red-200';
        if (status === '⚠️') className = 'bg-yellow-50 border-yellow-200';
        
        return (
          `<div class="mt-2 mb-2 border rounded-md overflow-hidden ${className}">
            <div class="p-2 font-medium text-sm border-b ${className}">${status} 工具 '${toolName}' ${result}</div>
            <pre class="p-3 text-sm bg-gray-50 overflow-x-auto whitespace-pre-wrap">${toolOutput}</pre>
          </div>`
        );
      }
    );
  }
  
  // 将剩余内容转换为Markdown
  return marked(processedContent);
};

// 处理按键事件，支持Enter发送
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  // 清除之前的错误
  error.value = null;

  // 添加用户消息
  const userMessage: ChatMessage = { 
    role: "user", 
    content: inputMessage.value,
    time: new Date()
  };
  
  messages.value.push(userMessage);
  emit("send", userMessage);

  // 清空输入框
  const messageToSend = inputMessage.value;
  inputMessage.value = "";

  // 设置加载状态
  isLoading.value = true;

  try {
    // 准备请求数据
    const requestData: MCPChatRequest = {
      message: messageToSend,
      sessionId: sessionId.value,
      modelType: "deepseek",
      systemPrompt: props.initialSystemPrompt,
    };

    // 发送请求
    const response = await sendMCPChatMessage(requestData);

    // 保存会话ID
    if (response.sessionId) {
      sessionId.value = response.sessionId;
    }

    // 添加AI回复
    const aiMessage: ChatMessage = {
      content: response.response,
      role: "assistant",
      time: new Date(),
      has_tool_call: response.has_tool_call
    };

    messages.value.push(aiMessage);
  } catch (err: any) {
    console.error("发送消息失败:", err);
    error.value = err.message || "发送失败，请稍后重试";
  } finally {
    isLoading.value = false;
  }
};

// 关闭对话框
const handleClose = () => {
  emit("close");
  dialogVisible.value = false;
};

// 重置会话
const resetSession = () => {
  sessionId.value = undefined;
  messages.value = [{ content: "会话已重置", role: "assistant", time: new Date() }];
  error.value = null;
};

// 暴露方法给父组件
defineExpose({
  addMessage: (message: ChatMessage) => {
    messages.value.push({
      ...message,
      time: message.time || new Date()
    });
  },
  clearMessages: () => {
    messages.value = [{ content: "对话已重置", role: "assistant", time: new Date() }];
  },
  resetSession
});
</script>

<style>
.chat-dialog :deep(.el-dialog__body) {
  padding: 0;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

/* Markdown 样式 */
.markdown-body h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 1rem;
}

.markdown-body h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
}

.markdown-body h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.markdown-body p {
  margin-bottom: 0.5rem;
}

.markdown-body ul, .markdown-body ol {
  padding-left: 1.5rem;
  margin-bottom: 0.5rem;
}

.markdown-body ul {
  list-style-type: disc;
}

.markdown-body ol {
  list-style-type: decimal;
}

.markdown-body li {
  margin-bottom: 0.25rem;
}

.markdown-body code {
  padding: 0.2rem 0.4rem;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.markdown-body pre {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  overflow-x: auto;
}

.markdown-body pre code {
  padding: 0;
  background-color: transparent;
}

.markdown-body blockquote {
  padding-left: 1rem;
  border-left: 4px solid #e5e7eb;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1rem;
}

.markdown-body table th,
.markdown-body table td {
  border: 1px solid #e5e7eb;
  padding: 0.5rem;
}

.markdown-body table th {
  background-color: rgba(0, 0, 0, 0.05);
}

.markdown-body a {
  color: #3b82f6;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body img {
  max-width: 100%;
  height: auto;
}
</style>
