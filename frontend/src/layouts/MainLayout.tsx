import { Layout, Menu } from "antd";
import { Outlet } from "react-router-dom";
import {
  FileTextOutlined,
  ProjectOutlined,
  SettingOutlined,
} from "@ant-design/icons";

const { Header, Content, Sider } = Layout;

const MainLayout = () => {
  return (
    <Layout className="min-h-screen">
      <Header className="flex items-center px-6 bg-white shadow">
        <h1 className="text-xl font-bold text-blue-600">AI MindMap</h1>
      </Header>
      <Layout>
        <Sider width={200} className="bg-white">
          <Menu
            mode="inline"
            defaultSelectedKeys={["1"]}
            style={{ height: "100%" }}
            items={[
              {
                key: "1",
                icon: <FileTextOutlined />,
                label: "文本生成",
              },
              {
                key: "2",
                icon: <ProjectOutlined />,
                label: "对话生成",
              },
              {
                key: "3",
                icon: <SettingOutlined />,
                label: "设置",
              },
            ]}
          />
        </Sider>
        <Layout className="p-6">
          <Content className="bg-white rounded-lg min-h-[280px] p-6">
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
