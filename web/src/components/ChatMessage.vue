<template>
  <div
    :class="['mb-3 flex', message.role === 'user' ? 'justify-end' : '']"
  >
    <div
      v-if="
        !(
          isLoading &&
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
  </div>
</template>

<script setup lang="ts">
import { marked } from 'marked';
import type { ChatMessage as ChatMessageType } from '../types';

const props = defineProps<{
  message: ChatMessageType;
  isLoading: boolean;
}>();

// 格式化消息内容，处理MCP工具调用结果和Markdown
const formatMessageContent = (content: string, has_tool_call?: boolean) => {
  let processedContent = content;

  // 处理工具调用结果
  if (has_tool_call) {
    // 处理"调用中"的情况
    processedContent = content.replace(
      /(✅|❌|⚠️) 工具 '(.+?)' (调用中|调用结果|调用失败|不可用)([\s\S]*?)(?=\n(✅|❌|⚠️) 工具|\n等待AI修正参数|\n工具调用|\n已达到最大尝试次数|$)/g,
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

// 格式化时间
const formatTime = (time: Date) => {
  return `${time
    .getHours()
    .toString()
    .padStart(2, "0")}:${time.getMinutes().toString().padStart(2, "0")}`;
};
</script> 