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
              v-if="
                !(
                  isLoading &&
                  index === messages.length - 1 &&
                  !message.content.trim()
                ) || message.role === 'user'
              "
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

            <!-- 消息加载动画 -->
            <div
              v-if="
                isLoading &&
                index === messages.length - 1 &&
                !message.content.trim() &&
                message.role === 'assistant'
              "
              class="max-w-[70%] px-3.5 py-2.5 bg-white rounded-xl rounded-tl-sm shadow-sm"
            >
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>

          <div ref="messagesEndRef"></div>
        </div>

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
              :class="{ 'opacity-75': isLoading }"
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
import {
  ref,
  computed,
  watch,
  nextTick,
  defineProps,
  defineEmits,
  defineExpose,
  onMounted,
  getCurrentInstance,
} from "vue";
import { sendMCPChatMessage, sendStreamingMCPChatMessage } from "../api/chat";
import { ChatMessage, MCPChatRequest } from "../types";
import { marked } from "marked";

interface MCPService {
  name: string;
  url: string;
}

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: "对话",
  },
  initialSystemPrompt: {
    type: String,
    default: "",
  },
  availableMcpServices: {
    type: Array as () => MCPService[],
    default: () => [],
  },
});

const emit = defineEmits(["update:visible", "close", "send"]);

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
});

// MCP服务列表
const mcpServices = computed(() => {
  return props.availableMcpServices.length > 0
    ? props.availableMcpServices
    : [{ name: "默认服务", url: "" }];
});

// 当前选中的MCP服务
const selectedMcpService = ref("");

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
const messagesContainer = ref<HTMLElement | null>(null);
const messagesEndRef = ref<HTMLElement | null>(null);

// 加载状态和错误信息
const isLoading = ref(false);
const error = ref<string | null>(null);

// 会话ID - 为每个MCP服务单独维护一个会话ID
const sessionIds = ref<Record<string, string>>({});

// 当前会话ID
const currentSessionId = computed(() => {
  return sessionIds.value[selectedMcpService.value] || undefined;
});

// 流式输出相关
const currentStreamingMessage = ref<ChatMessage | null>(null); // 当前正在流式输出的消息
const app = getCurrentInstance(); // 获取Vue实例

// 在组件级别定义计时器变量
const updateTimer = ref<number | null>(null);

// 设置初始MCP服务
onMounted(() => {
  if (mcpServices.value.length > 0) {
    selectedMcpService.value = mcpServices.value[0].url;
  }

  // 配置 marked 选项
  marked.setOptions({
    breaks: true, // 支持换行符转换为 <br>
    gfm: true, // 启用 GitHub 风格的 Markdown
  });
});

// 强制DOM更新
const forceUpdate = () => {
  if (app && app.proxy) {
    app.proxy.$forceUpdate();
  }
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

// 格式化时间
const formatTime = (time: Date) => {
  return `${time
    .getHours()
    .toString()
    .padStart(2, "0")}:${time.getMinutes().toString().padStart(2, "0")}`;
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
        let className = "";
        if (status === "✅") className = "bg-green-50 border-green-200";
        if (status === "❌") className = "bg-red-50 border-red-200";
        if (status === "⚠️") className = "bg-yellow-50 border-yellow-200";

        return `<div class="mt-2 mb-2 border rounded-md overflow-hidden ${className}">
            <div class="p-2 font-medium text-sm border-b ${className}">${status} 工具 '${toolName}' ${result}</div>
            <pre class="p-3 text-sm bg-gray-50 overflow-x-auto whitespace-pre-wrap">${toolOutput}</pre>
          </div>`;
      }
    );
  }

  // 将剩余内容转换为Markdown
  return marked(processedContent);
};

// 处理按键事件，支持Enter发送
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === "Enter" && !e.shiftKey) {
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
    time: new Date(),
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
      sessionId: currentSessionId.value,
      modelType: "deepseek",
      systemPrompt: props.initialSystemPrompt,
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
          // 更新消息内容
          currentStreamingMessage.value.content += chunk;
          console.log("收到数据块:", chunk);
          
          // 更新工具调用标记
          if (hasToolCall) {
            currentStreamingMessage.value.has_tool_call = true;
          }

          // 只有当有实际内容时才更新UI
          if (chunk.trim()) {
            // 清除之前的计时器
            if (updateTimer.value) {
              clearTimeout(updateTimer.value);
            }
            
            // 立即执行一次更新
            forceUpdate();
            scrollToBottom();

            // 设置新的计时器
            updateTimer.value = window.setTimeout(() => {
              forceUpdate();
              scrollToBottom();
              updateTimer.value = null;
            }, 50);
          }

          // 完成时更新状态
          if (isComplete) {
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

            // 最后再强制更新一次
            forceUpdate();
            scrollToBottom();
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
      content: `已切换到 ${
        mcpServices.value.find((s) => s.url === serviceUrl)?.name || "新"
      } MCP服务`,
      role: "assistant",
      time: new Date(),
    },
  ];
};

// 暴露方法给父组件
defineExpose({
  addMessage: (message: ChatMessage) => {
    messages.value.push({
      ...message,
      time: message.time || new Date(),
    });
  },
  clearMessages: () => {
    messages.value = [{ content: "对话已重置", role: "assistant", time: new Date() }];
  },
  resetSession,
  switchMcpService,
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

/* 添加加载动画样式 */
.loading-dots {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 20px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background-color: #909399;
  border-radius: 50%;
  margin: 0 4px;
  animation: blink 1.4s infinite both;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0% {
    opacity: 0.2;
  }
  20% {
    opacity: 1;
  }
  40% {
    opacity: 0.2;
  }
  60% {
    opacity: 1;
  }
  80% {
    opacity: 0.2;
  }
  100% {
    opacity: 1;
  }
}

.markdown-body {
  transform: translateZ(0);
  will-change: contents;
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

.markdown-body ul,
.markdown-body ol {
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
