import React, { useState } from "react";
import { MindMap } from "../components/MindMap";
import DocumentUpload from "../components/DocumentUpload";
import { TextInput } from "../components/TextInput";
import type { MindMapNode } from "../api/mindmap";
import { Card, Tabs, Typography } from "antd";

const { TabPane } = Tabs;
const { Title, Paragraph } = Typography;

const MindMapPage: React.FC = () => {
  const [mindmapData, setMindmapData] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="mindmap-page">
      <div className="page-header">
        <div className="logo-section">
          <img src="/logo.svg" alt="logo" className="logo-icon" />
          <Title level={2} style={{ margin: 0 }}>
            AI 思维导图生成器
          </Title>
        </div>
        <Paragraph className="subtitle">
          瞬间将各种想法转化为直观的思维导图，支持文字、PDF、视频等多种输入形式。
        </Paragraph>
      </div>

      <Card bordered={false} className="main-content">
        <Tabs
          defaultActiveKey="text"
          items={[
            {
              key: "text",
              label: "一句话",
              children: (
                <TextInput
                  onMindMapGenerated={setMindmapData}
                  onLoading={setLoading}
                />
              ),
            },
            {
              key: "pdf",
              label: "PDF/文档",
              children: <DocumentUpload onMindMapGenerated={setMindmapData} />,
            },
            {
              key: "article",
              label: "长文本",
              children: (
                <TextInput
                  onMindMapGenerated={setMindmapData}
                  onLoading={setLoading}
                />
              ),
            },
            {
              key: "website",
              label: "网站",
              disabled: true,
            },
            {
              key: "youtube",
              label: "YouTube",
              disabled: true,
            },
            {
              key: "image",
              label: "图片",
              disabled: true,
            },
          ]}
        />
      </Card>

      {mindmapData && !loading && (
        <Card className="mindmap-result">
          <MindMap markdown={mindmapData} />
        </Card>
      )}
    </div>
  );
};

export default MindMapPage;
