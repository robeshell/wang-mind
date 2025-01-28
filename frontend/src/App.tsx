import React, { useState } from "react";
import { Layout, Tabs, Input, Button, message } from "antd";
import { LogoIcon, EyeIcon } from "./components/Icons";
import DocumentUpload from "./components/DocumentUpload";
import TextInput from "./components/TextInput";
import "./App.css";

const { Content } = Layout;
const { TextArea } = Input;

const App: React.FC = () => {
  const [mindmapData, setMindmapData] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleMindMapGenerated = (data: string) => {
    setMindmapData(data);
  };

  const tabItems = [
    {
      key: "text",
      label: "文本输入",
      children: <TextInput onMindMapGenerated={handleMindMapGenerated} />,
    },
    {
      key: "upload",
      label: "上传文档",
      children: <DocumentUpload onMindMapGenerated={handleMindMapGenerated} />,
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
            <Tabs defaultActiveKey="text" items={tabItems} />
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default App;
