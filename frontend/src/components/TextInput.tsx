import React, { useState } from "react";
import { Input, Button, message } from "antd";
import { generateMindMapFromText } from "../api/mindmap";

const { TextArea } = Input;

interface TextInputProps {
  onMindMapGenerated: (data: string) => void;
  onLoading?: (loading: boolean) => void;
}

export const TextInput: React.FC<TextInputProps> = ({
  onMindMapGenerated,
  onLoading,
}) => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!text.trim()) {
      message.warning("请输入文本内容");
      return;
    }

    setLoading(true);
    onLoading?.(true);

    try {
      const response = await generateMindMapFromText(text);
      if (response.success && response.data) {
        onMindMapGenerated(response.data);
        message.success("思维导图生成成功");
      } else {
        message.error(response.error || "生成失败");
      }
    } catch (error) {
      console.error("生成思维导图失败:", error);
      message.error("生成思维导图失败，请重试");
    } finally {
      setLoading(false);
      onLoading?.(false);
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
      >
        生成思维导图
      </Button>
    </div>
  );
};
