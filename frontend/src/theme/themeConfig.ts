import type { ThemeConfig } from "antd";

const theme: ThemeConfig = {
  token: {
    fontSize: 16,
    colorPrimary: "#1677ff",
  },
  components: {
    Layout: {
      headerBg: "#ffffff",
      headerHeight: 64,
      headerPadding: "0 50px",
    },
    Card: {
      paddingLG: 24,
    },
  },
};

export default theme;
