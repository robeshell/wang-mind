import React, { useState } from "react";
import { Input, Button, message } from "antd";
import MarkdownMindmap from "./MarkdownMindmap";

const { TextArea } = Input;

interface TextInputProps {
  onMindMapGenerated: (data: string) => void;
}

const TextInput: React.FC<TextInputProps> = ({ onMindMapGenerated }) => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [generatingContent, setGeneratingContent] = useState("");
  const [reasoningContent, setReasoningContent] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (log: string, type: "info" | "error" = "info") => {
    console.log(`[${type}] ${log}`);
    setLogs((prev) => [...prev, log]);
  };

  const handleGenerate = async () => {
    if (!text.trim()) {
      message.warning("请输入文本内容");
      return;
    }

    setLoading(true);
    setGeneratingContent("");
    setReasoningContent("");
    setLogs([]);

    try {
      const response = await fetch("/api/v1/mindmap/from-text/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ content: text }),
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
                        setGeneratingContent(accumulatedContent);
                        onMindMapGenerated(accumulatedContent);
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
                    onMindMapGenerated(data.data);
                    message.success("思维导图生成成功");
                  }
                  setLoading(false);
                  break;
                case "error":
                  console.error("处理错误:", data.message);
                  addLog(`错误: ${data.message}`, "error");
                  message.error(data.message);
                  setLoading(false);
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
      setLoading(false);
    }
  };

  return (
    <div className="text-input">
      <TextArea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="请输入要生成思维导图的文本内容..."
        autoSize={{ minRows: 4, maxRows: 8 }}
      />
      <Button
        type="primary"
        onClick={handleGenerate}
        loading={loading}
        disabled={!text.trim()}
        className="mt-4"
      >
        生成思维导图
      </Button>

      {loading && (
        <div className="upload-status mt-4">
          <div className="logs">
            {logs.map((log, index) => (
              <div key={index} className="log-item">
                {log}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-col gap-4 mt-4">
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

export default TextInput;
