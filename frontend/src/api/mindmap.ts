import axios from "axios";
import { message } from "antd";

// 修改 axios 默认值
axios.defaults.baseURL = "/api/v1";
axios.defaults.timeout = 60000;
axios.defaults.headers.post["Content-Type"] = "application/json";

// 添加请求拦截器
axios.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 添加响应拦截器
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.code === "ECONNABORTED" && error.message.includes("timeout")) {
      message.error("请求超时，请重试");
    } else if (error.response) {
      message.error(error.response.data?.error || "请求失败");
    } else {
      message.error("网络错误，请检查网络连接");
    }
    return Promise.reject(error);
  }
);

export interface MindMapNode {
  id: string;
  label: string;
  children?: MindMapNode[];
}

export interface DocumentAnalysisResponse {
  success: boolean;
  data?: MindMapNode;
  error?: string;
}

export interface MindMapResponse {
  success: boolean;
  data?: string; // markdown string
  error?: string;
}

/**
 * 处理 PDF 文件并返回 EventSource
 */
export const processPDF = async (file: File): Promise<EventSource> => {
  try {
    // 读取文件内容
    const base64Content = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        const base64 = result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

    // 创建请求体
    const requestBody = {
      content: base64Content,
      doc_type: "pdf",
      title: file.name.replace(".pdf", ""),
      max_depth: 3,
    };

    // 使用 POST 请求
    const response = await fetch("/api/v1/mindmap/from-document/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 创建 EventSource 连接
    const eventSource = new EventSource("/api/v1/mindmap/from-document/stream");

    // 添加错误处理
    eventSource.onerror = (error) => {
      console.error("SSE 连接错误:", error);
      eventSource.close();
      message.error("连接失败，请重试");
    };

    return eventSource;
  } catch (error) {
    console.error("处理 PDF 失败:", error);
    message.error("处理 PDF 失败，请重试");
    throw error;
  }
};

/**
 * 从文本生成思维导图
 */
export const generateMindMapFromText = async (
  text: string
): Promise<MindMapResponse> => {
  try {
    const response = await fetch("/api/v1/mindmap/from-text", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ content: text }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("生成思维导图失败:", error);
    throw error;
  }
};

/**
 * 健康检查
 */
export const checkHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch("/api/v1/mindmap/health");
    return response.ok;
  } catch (error) {
    console.error("健康检查失败:", error);
    return false;
  }
};
