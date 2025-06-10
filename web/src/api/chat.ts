import axios from "axios";
import { MCPChatRequest, MCPChatResponse } from "../types";

const API_BASE_URL = "/api";

/**
 * 增强版聊天API - 支持多轮对话和MCP工具调用
 */
export const sendMCPChatMessage = async (
  data: MCPChatRequest
): Promise<MCPChatResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/chat/msg`, data);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    throw error;
  }
};

export default {
  sendMCPChatMessage,
};
