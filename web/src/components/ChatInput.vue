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
        @click="handleSendClick"
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

    <!-- 验证弹窗 -->
    <el-dialog
      v-model="showVerificationDialog"
      title="安全验证"
      width="30%"
      :close-on-click-modal="false"
    >
      <div>
        <p class="mb-3">为防止恶意使用，请输入验证码。请问作者的博客地址是？(xxxx.xxx 格式)</p>
        <el-input 
          v-model="verificationCode" 
          placeholder="请输入验证码"
          class="mb-4"
        ></el-input>
        <div class="text-red-500 text-sm mb-3" v-if="verificationError">
          {{ verificationError }}
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showVerificationDialog = false">取消</el-button>
          <el-button type="primary" @click="verifyAndSend">
            确认发送
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

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

// 验证相关状态
const showVerificationDialog = ref(false);
const verificationCode = ref('');
const verificationError = ref('');

const VERIFICATION_SECRET = 'flands.cn'; // 验证码，可以根据需求修改

// 处理按键事件，支持Enter发送
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSendClick();
  }
};

// 处理发送按钮点击
const handleSendClick = () => {
  if (!inputValue.value.trim() || props.isLoading) return;
  
  // 显示验证弹窗
  verificationCode.value = '';
  verificationError.value = '';
  showVerificationDialog.value = true;
};

// 验证并发送
const verifyAndSend = () => {
  if (verificationCode.value === VERIFICATION_SECRET) {
    showVerificationDialog.value = false;
    sendMessage();
  } else {
    verificationError.value = '验证码错误，请重新输入';
  }
};

// 发送消息
const sendMessage = () => {
  if (!inputValue.value.trim() || props.isLoading) return;
  emit('send');
};
</script> 