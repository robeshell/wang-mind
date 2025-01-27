from pathlib import Path

# 忽略的文件和目录
ignore_dirs = {
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "venv",
    "node_modules",
}

# 只监视这些扩展名的文件
watch_file_extensions = {".py", ".json", ".yaml", ".yml"}

def should_reload(path: Path) -> bool:
    """决定是否需要重载的函数"""
    # 忽略特定目录
    if any(part in ignore_dirs for part in path.parts):
        return False
        
    # 只监视特定扩展名
    if path.suffix not in watch_file_extensions:
        return False
        
    return True 