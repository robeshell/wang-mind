import React, { useState } from "react";
import { Layout, Tabs, Input, Button, message } from "antd";
import { LogoIcon, EyeIcon } from "./components/Icons";
import DocumentUpload from "./components/DocumentUpload";
import MarkdownMindmap from "./components/MarkdownMindmap";
import "./App.css";

const { Content } = Layout;
const { TextArea } = Input;

const App: React.FC = () => {
  const [mindmapData, setMindmapData] = useState<string>("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleMindMapGenerated = (data: string) => {
    setMindmapData(data);
  };

  const handleTextSubmit = async () => {
    if (!text.trim()) {
      message.warning("请输入文本内容");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/v1/mindmap/from-text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ content: text }),
      });

      if (!response.ok) {
        throw new Error("请求失败");
      }

      const data = await response.json();
      setMindmapData(data.mindmap);
      message.success("思维导图生成成功");
    } catch (error) {
      message.error("生成失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  const handleYoutubeSubmit = async (url: string) => {
    if (!url.trim()) {
      message.warning("请输入YouTube链接");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/v1/mindmap/from-youtube", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error("请求失败");
      }

      const data = await response.json();
      setMindmapData(data.mindmap);
      message.success("思维导图生成成功");
    } catch (error) {
      message.error("生成失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  const tabItems = [
    {
      key: "upload",
      label: "上传文档",
      children: <DocumentUpload onMindMapGenerated={handleMindMapGenerated} />,
    },
    {
      key: "text",
      label: "文本输入",
      children: (
        <div className="text-input">
          <TextArea
            rows={6}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="请输入要分析的文本内容..."
          />
          <Button type="primary" onClick={handleTextSubmit} loading={loading}>
            生成思维导图
          </Button>
        </div>
      ),
    },
    {
      key: "youtube",
      label: "YouTube视频",
      children: (
        <div className="text-input">
          <Input
            placeholder="请输入YouTube视频链接..."
            onPressEnter={(e) => handleYoutubeSubmit(e.currentTarget.value)}
          />
          <Button
            type="primary"
            onClick={() => {
              const input = document.querySelector(
                'input[placeholder="请输入YouTube视频链接..."]'
              ) as HTMLInputElement;
              handleYoutubeSubmit(input.value);
            }}
            loading={loading}
          >
            生成思维导图
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Layout className="app-layout">
      <Content className="app-content">
        <div className="mindmap-page">
          <div className="page-header">
            <div className="logo-section">
              <LogoIcon className="logo-icon" />
              <div className="title-group">
                <h1>AI 思维导图生成器</h1>
                <h2>让想法一目了然</h2>
              </div>
              <EyeIcon className="eye-icon" />
            </div>
            <p className="subtitle">
              瞬间将各种想法转化为直观的思维导图，支持文字、PDF、视频等多种输入形式。
            </p>
          </div>
          <div className="main-content">
            <Tabs defaultActiveKey="upload" items={tabItems} />
            {mindmapData && (
              <div className="mindmap-container">
                <MarkdownMindmap
                  markdown={mindmapData}
                  key={mindmapData.length}
                />
              </div>
            )}
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default App;
