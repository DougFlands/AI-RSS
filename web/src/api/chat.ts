import axios from "axios";
import { MCPChatRequest } from "../types";

const API_BASE_URL = "/api";

/**
 * 使用 axios 实现 SSE 流式响应
 * @param data 聊天请求数据
 * @param onChunk 处理流式响应块的回调函数
 * @returns Promise<{sessionId: string}> 包含会话ID的Promise
 */
export const sendStreamingMCPChatMessage = async (
  data: MCPChatRequest,
  onChunk: (chunk: string, isComplete: boolean, hasToolCall: boolean) => void
): Promise<{ sessionId: string }> => {
  return new Promise((resolve, reject) => {
    let sessionId = data.sessionId || "";
    let hasToolCall = false;
    let buffer = "";

    // 创建 axios 请求配置
    const config = {
      method: "post",
      url: `${API_BASE_URL}/chat/stream`,
      data: {
        ...data,
        createStream: true,
      },
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
      responseType: "stream" as any,
      onDownloadProgress: (progressEvent: any) => {
        // 获取新到达的文本数据
        const rawText = progressEvent.event.target.response || "";
        // 如果有新数据
        if (rawText && rawText !== buffer) {
          // 提取新增部分
          const newText = rawText.substring(buffer.length);
          buffer = rawText; // 更新缓冲区

          // 处理新增的 SSE 数据
          const lines = newText.split("\n\n");

          for (const line of lines) {
            if (!line.trim()) continue;

            // 提取 data: 部分
            const match = line.match(/data: (.*)/);
            if (!match) continue;

            try {
              const eventData = JSON.parse(match[1]);
              console.log("收到SSE数据:", eventData);

              if (eventData.type === "chunk") {
                // 处理文本块
                onChunk(eventData.content, false, hasToolCall);
              } else if (eventData.type === "tool_call") {
                // 工具调用标记
                hasToolCall = true;
                onChunk("", false, true);
              } else if (eventData.type === "session_id") {
                // 保存会话ID
                sessionId = eventData.session_id;
                console.log("获取到会话ID:", sessionId);
              } else if (eventData.type === "end") {
                // 流结束
                console.log("流式输出结束");
                onChunk("", true, hasToolCall);
                resolve({ sessionId });
              } else if (eventData.type === "error") {
                // 错误处理
                console.error("流处理错误:", eventData.error);
                onChunk(`错误: ${eventData.error}`, false, hasToolCall);
              }
            } catch (error) {
              console.error("解析流事件失败:", error, "原始数据:", line);
            }
          }
        }
      },
    };

    // 发送请求
    axios(config)
      .then(() => {
        // 请求完成，如果没有通过 end 事件解析，在这里解析
        if (sessionId) {
          resolve({ sessionId });
        } else {
          resolve({ sessionId: "" });
        }
      })
      .catch((error) => {
        console.error("SSE请求失败:", error);
        reject(error);
      });
  });
};

export const streamChat = {
  sendStreamingMCPChatMessage,
};

export default {
  sendStreamingMCPChatMessage,
};
