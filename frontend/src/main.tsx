import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import App from "./App";
// 导入 Ant Design 样式
import "antd/dist/reset.css";
// 导入 Tailwind CSS
import "./styles/index.css";
// 导入自定义样式
import "./App.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
