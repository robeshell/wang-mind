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
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [generatingContent, setGeneratingContent] = useState<string>("");

  const addLog = (log: string, type: "info" | "error" = "info") => {
    console.log(`[${type}] ${log}`);
    setLogs((prev) => [...prev, log]);
  };

  const handleSSE = async (file: RcFile) => {
    setUploading(true);
    setGeneratingContent("");
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
        let mindmapContent = "";

        while (reader) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value);
          const lines = text.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                console.log(`[${data.type}]`, data.message || "");

                switch (data.type) {
                  case "start":
                    addLog(`开始处理: ${data.message}`);
                    break;
                  case "progress":
                    setProgress(data.progress || 0);
                    break;
                  case "generating":
                    if (data.partial) {
                      setGeneratingContent((prev) => {
                        const newContent = prev + data.partial;
                        if (data.partial.includes("\n")) {
                          console.log(
                            "更新节点数:",
                            newContent.split("\n").length - 1
                          );
                        }
                        return newContent;
                      });
                    }
                    break;
                  case "complete":
                    if (data.data) {
                      setGeneratingContent(data.data);
                      message.success("思维导图生成成功");
                    }
                    setUploading(false);
                    break;
                  case "error":
                    addLog(`错误: ${data.message}`, "error");
                    message.error(data.message);
                    setUploading(false);
                    break;
                }
              } catch (e) {
                console.error("解析消息失败:", e, line);
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
            <Progress percent={Math.round(progress)} />
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

      <div className="mindmap-container">
        {generatingContent && (
          <MarkdownMindmap
            markdown={generatingContent}
            key={generatingContent.length}
          />
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;
