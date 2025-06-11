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
        <div class="flex-1 p-4 overflow-y-auto bg-gray-50">
          <template v-for="(message, index) in chatMessages" :key="index">
            <ChatMessage 
              :message="message"
              :is-loading="isLoading"
            />
          </template>

          <!-- 最下方的加载动画，只在加载时显示 -->
          <ChatLoading v-if="isLoading" />

          <div ref="messagesEndRef"></div>
        </div>

        <!-- 输入区域 -->
        <ChatInput 
          :input-message="inputMessage"
          @update:input-message="updateInputMessage"
          :is-loading="isLoading"
          :error="errorMessage"
          @send="handleSendMessage"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  defineProps,
  defineEmits,
  defineExpose,
  onMounted,
  ref,
  watch
} from "vue";
import { useChat } from "../composables/useChat";
import ChatMessage from "./ChatMessage.vue";
import ChatInput from "./ChatInput.vue";
import ChatLoading from "./ChatLoading.vue";
import type { ChatMessage as ChatMessageType } from "../types";
import '../assets/styles/markdown.css';

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

// 获取Vue实例
const app = getCurrentInstance();
const messagesEndRef = ref<HTMLElement | null>(null);

// 强制DOM更新
const forceUpdate = () => {
  if (app && app.proxy) {
    app.proxy.$forceUpdate();
  }
};

// 使用聊天钩子
const chat = useChat(props.initialSystemPrompt);

// 创建计算属性来获取最新值
const chatMessages = computed(() => chat.messages.value);
const inputMessage = computed(() => chat.inputMessage.value);
const isLoading = computed(() => chat.isLoading.value);
const errorMessage = computed(() => chat.error.value);

// 更新输入消息的方法
const updateInputMessage = (value: string) => {
  chat.inputMessage.value = value;
};

// 滚动到底部的函数
const scrollToBottom = () => {
  if (messagesEndRef.value) {
    messagesEndRef.value.scrollIntoView({ behavior: "smooth" });
  }
};

// 监听消息变化，自动滚动到底部
watch(chatMessages, () => {
  scrollToBottom();
}, { deep: true });

// 设置初始MCP服务
onMounted(() => {
  if (mcpServices.value.length > 0) {
    chat.selectedMcpService.value = mcpServices.value[0].url;
  }
  
  // 使用本地的scrollToBottom方法
  chat.messagesEndRef.value = messagesEndRef.value;
});

// 发送消息处理函数
const handleSendMessage = async () => {
  emit("send", { 
    role: "user", 
    content: chat.inputMessage.value, 
    time: new Date() 
  });
  
  await chat.sendMessage(forceUpdate);
};

// 关闭对话框
const handleClose = () => {
  emit("close");
  dialogVisible.value = false;
};

// 切换MCP服务
const switchMcpService = (serviceUrl: string) => {
  chat.switchMcpService(serviceUrl);
};

// 暴露方法给父组件
defineExpose({
  addMessage: (message: ChatMessageType) => {
    chat.addMessage(message);
  },
  clearMessages: () => {
    chat.clearMessages();
  },
  resetSession: () => {
    chat.resetSession();
  },
  switchMcpService
});
</script>

<style>
.chat-dialog :deep(.el-dialog__body) {
  padding: 0;
}
</style>
