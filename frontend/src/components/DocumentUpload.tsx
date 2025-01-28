import React, { useState, useEffect } from "react";
import {
  Upload,
  Button,
  message,
  Spin,
  Drawer,
  Typography,
  Progress,
} from "antd";
import { UploadOutlined, BugOutlined, InboxOutlined } from "@ant-design/icons";
import type { UploadFile, RcFile } from "antd/es/upload/interface";
import type { MindMapNode } from "../api/mindmap";
import MarkdownMindmap from "./MarkdownMindmap";

const { Text } = Typography;

interface DocumentUploadProps {
  onMindMapGenerated: (data: string) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onMindMapGenerated,
}) => {
  const [uploading, setUploading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [generatingContent, setGeneratingContent] = useState<string>("");
  const [reasoningContent, setReasoningContent] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const addLog = (log: string, type: "info" | "error" = "info") => {
    console.log(`[${type}] ${log}`);
    setLogs((prev) => [...prev, log]);
  };

  const handleSSE = async (file: RcFile) => {
    setUploading(true);
    setGeneratingContent("");
    setReasoningContent("");
    setLogs([]);

    const reader = new FileReader();

    reader.onload = async (e) => {
      try {
        const base64Content = (e.target?.result as string).split(",")[1];
        const requestData = {
          content: base64Content,
          doc_type: "pdf",
          title: file.name,
        };

        const response = await fetch("/api/v1/mindmap/from-document/stream", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestData),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        let accumulatedContent = "";
        let currentLine = "";

        while (reader) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value);

          const lines = text.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));

                switch (data.type) {
                  case "start":
                    addLog(`开始处理: ${data.message}`);
                    break;
                  case "reasoning":
                    setReasoningContent(prev => prev + data.partial);
                    break;
                  case "generating":
                    if (data.partial) {
                      if (data.partial.includes("<think>")) {
                        setReasoningContent(prev => prev + data.partial.replace("<think>", ""));
                      } else {
                        currentLine += data.partial;
                        if (data.partial.includes("\n")) {
                          accumulatedContent += currentLine;
                          if (currentLine.startsWith("# ")) {
                            console.log("根节点:", currentLine.trim());
                          }
                          setGeneratingContent(accumulatedContent);
                          currentLine = "";
                        }
                      }
                    }
                    break;
                  case "complete":
                    if (data.data) {
                      if (currentLine) {
                        accumulatedContent += currentLine;
                      }
                      setGeneratingContent(data.data);
                      setReasoningContent(data.reasoning);
                      message.success("思维导图生成成功");
                    }
                    setUploading(false);
                    break;
                  case "error":
                    console.error("处理错误:", data.message);
                    addLog(`错误: ${data.message}`, "error");
                    message.error(data.message);
                    setUploading(false);
                    break;
                }
              } catch (e) {
                console.error("解析 SSE 消息失败:", e, line);
              }
            }
          }
        }
      } catch (error) {
        console.error("处理失败:", error);
        message.error("处理失败，请重试");
        setUploading(false);
      }
    };

    reader.readAsDataURL(file);
    return false;
  };

  return (
    <div className="document-upload">
      <div className="upload-area">
        <Upload.Dragger
          accept=".pdf"
          beforeUpload={handleSSE}
          showUploadList={false}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">支持 PDF 文件</p>
        </Upload.Dragger>

        {uploading && (
          <div className="upload-status">
            <div className="logs">
              {logs.map((log, index) => (
                <div key={index} className="log-item">
                  {log}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-4">
        {reasoningContent && (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium mb-2">思维过程</h3>
            <pre style={{
              whiteSpace: 'pre-line',
              lineHeight: '1.6',
              wordBreak: 'break-word',
              margin: '0',
              padding: '8px'
            }}>
              {reasoningContent}
            </pre>
          </div>
        )}
        <div className="mindmap-container">
          <MarkdownMindmap markdown={generatingContent} />
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
