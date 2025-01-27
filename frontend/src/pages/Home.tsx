import { useState } from "react";
import { Input, Button, Card, Space, message } from "antd";
import { SendOutlined } from "@ant-design/icons";
import MindMap from "@/components/MindMap";

const { TextArea } = Input;

const Home = () => {
  const [inputText, setInputText] = useState("");
  const [mindMapData, setMindMapData] = useState({
    id: "root",
    label: "思维导图",
    children: [],
  });

  const handleGenerate = async () => {
    if (!inputText.trim()) {
      message.warning("请输入内容");
      return;
    }
    // TODO: 实现生成脑图的逻辑
    try {
      // 这里模拟API调用
      const mockData = {
        id: "root",
        label: "主题",
        children: [
          {
            id: "sub1",
            label: "子主题1",
          },
          {
            id: "sub2",
            label: "子主题2",
            children: [
              {
                id: "sub2-1",
                label: "子主题2.1",
              },
            ],
          },
        ],
      };
      setMindMapData(mockData);
      message.success("生成成功");
    } catch (error) {
      console.error("生成脑图失败:", error);
      message.error("生成失败，请重试");
    }
  };

  return (
    <div>
      <Card
        title="文本生成脑图"
        extra={
          <Space>
            <Button>清空</Button>
            <Button>导出</Button>
          </Space>
        }
      >
        <TextArea
          rows={6}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="输入文本内容..."
          className="mb-4"
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleGenerate}
          size="large"
        >
          生成脑图
        </Button>
      </Card>
      <div className="mt-6 bg-gray-50 p-6 rounded-lg min-h-[500px] border">
        <MindMap data={mindMapData} />
      </div>
    </div>
  );
};

export default Home;
