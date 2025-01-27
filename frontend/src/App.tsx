import React from "react";
import { Layout } from "antd";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import MindMapPage from "./pages/MindMapPage";
import "./App.css";

const { Content } = Layout;

const App: React.FC = () => {
  return (
    <Router>
      <Layout className="app-layout">
        <Content className="app-content">
          <Routes>
            <Route path="/" element={<MindMapPage />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  );
};

export default App;
