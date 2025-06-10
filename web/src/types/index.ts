export interface ChatMessage {
  role: string;
  content: string;
  has_tool_call?: boolean;
  time?: Date;
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
  modelType?: string;
  systemPrompt?: string;
}

export interface MCPChatRequest extends ChatRequest {
  mcpUrl?: string;
}

export interface MCPChatResponse {
  sessionId: string;
  response: string;
  history: ChatMessage[];
  has_tool_call?: boolean;
  error?: string;
} 