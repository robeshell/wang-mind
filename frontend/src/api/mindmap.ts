/**
 * 健康检查
 */
export const checkHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch("/api/v1/mindmap/health");
    return response.ok;
  } catch (error) {
    console.error("健康检查失败:", error);
    return false;
  }
};
