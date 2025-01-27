import { Routes, Route } from "react-router-dom";
import Layout from "@/layouts/MainLayout";
import Home from "@/pages/Home";

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
