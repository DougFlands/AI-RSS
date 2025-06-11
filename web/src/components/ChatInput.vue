<template>
  <div class="p-4 bg-white border-t border-gray-200">
    <div class="flex">
      <el-input
        v-model="inputValue"
        placeholder="请输入消息..."
        @keydown="handleKeyDown"
        :disabled="isLoading"
        type="textarea"
      ></el-input>
      <el-button
        @click="sendMessage"
        :disabled="!inputValue.trim() || isLoading"
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
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  inputMessage: string;
  isLoading: boolean;
  error: string | null;
}>();

const emit = defineEmits<{
  (e: 'update:inputMessage', value: string): void;
  (e: 'send'): void;
}>();

const inputValue = computed({
  get: () => props.inputMessage,
  set: (value) => emit('update:inputMessage', value)
});

// 处理按键事件，支持Enter发送
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

// 发送消息
const sendMessage = () => {
  if (!inputValue.value.trim() || props.isLoading) return;
  emit('send');
};
</script> 