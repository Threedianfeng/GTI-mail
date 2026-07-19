"""文件操作模块 - 三角洲行动文件改名/恢复逻辑"""

import os
import threading

TARGET_PAK = "pak-0-2-pakchunk90-WindowsClient.pak"
CHANGGONG_NAME = "长工.text"
RELATIVE_PATH = os.path.join("DeltaForce", "PackContent", "Paks")

# 跳过这些系统目录以加速全盘搜索
_SKIP_DIRS = {
    "Windows", "ProgramData", "System Volume Information",
    "$Recycle.Bin", "Recovery", "Config.Msi", "MSOCache",
}


def _normalize_name(name: str) -> str:
    """将名称转为小写并移除所有空格，用于大小写和空格不敏感的匹配"""
    return name.lower().replace(" ", "")


def _is_delta_force_dir(name: str) -> bool:
    """判断文件夹名称是否匹配 'Delta Force'（忽略大小写和空格差异）"""
    return "deltaforce" in _normalize_name(name)


def find_delta_force_parent(root_dir: str) -> str | None:
    """检查根目录的上级目录是否就是 Delta Force 文件夹。

    如果用户输入的根目录上一级是 Delta Force 文件夹，
    则直接返回该上级目录，无需再向下遍历。

    Args:
        root_dir: 用户指定的根目录路径

    Returns:
        上级 Delta Force 文件夹路径，若不匹配则返回 None
    """
    parent = os.path.dirname(os.path.abspath(root_dir))
    if parent == root_dir:
        return None
    if _is_delta_force_dir(os.path.basename(parent)):
        return parent
    return None


def find_deepest_delta_force(root_dir: str) -> str | None:
    """从 root_dir 开始，递归查找名称包含 'Delta Force' 的最深层文件夹。

    每次找到含 'Delta Force' 的子文件夹后，进入该文件夹继续查找，
    直到当前文件夹内不再包含任何名称含 'Delta Force' 的子文件夹为止。
    匹配时忽略大小写和空格差异。

    Args:
        root_dir: 用户指定的根目录路径

    Returns:
        最深层的 Delta Force 文件夹路径，若未找到则返回 None
    """
    current = root_dir
    while True:
        try:
            entries = os.listdir(current)
        except OSError:
            return None

        # 查找当前目录下所有名称含 "Delta Force" 的子文件夹（忽略大小写和空格）
        delta_dirs = [
            d for d in entries
            if os.path.isdir(os.path.join(current, d)) and _is_delta_force_dir(d)
        ]

        if not delta_dirs:
            if _is_delta_force_dir(os.path.basename(current)):
                return current
            return None

        # 进入第一个找到的 Delta Force 文件夹，继续深入
        current = os.path.join(current, delta_dirs[0])


def _get_pak_path(base_path: str) -> str:
    """拼接目标 .pak 文件的完整路径"""
    return os.path.join(base_path, RELATIVE_PATH, TARGET_PAK)


def _get_changgong_path(base_path: str) -> str:
    """拼接改名后文件的完整路径"""
    return os.path.join(base_path, RELATIVE_PATH, CHANGGONG_NAME)


def rename_to_changgong(base_path: str) -> tuple[bool, str]:
    """将目标 .pak 文件改名为 长工.text

    Args:
        base_path: 最深层的 Delta Force 文件夹路径

    Returns:
        (success, message): 操作结果和说明信息
    """
    pak_path = _get_pak_path(base_path)
    changgong_path = _get_changgong_path(base_path)

    if os.path.exists(changgong_path):
        return True, "文件已经是改名状态，无需重复操作"

    if not os.path.exists(pak_path):
        return False, f"目标文件不存在: {pak_path}"

    os.rename(pak_path, changgong_path)
    return True, "改名成功"


def restore_from_changgong(base_path: str) -> tuple[bool, str]:
    """将 长工.text 恢复为原始 .pak 文件名

    Args:
        base_path: 最深层的 Delta Force 文件夹路径

    Returns:
        (success, message): 操作结果和说明信息
    """
    pak_path = _get_pak_path(base_path)
    changgong_path = _get_changgong_path(base_path)

    if os.path.exists(pak_path):
        return True, "文件已经是原始状态，无需重复操作"

    if not os.path.exists(changgong_path):
        return False, f"未找到改名文件: {changgong_path}"

    os.rename(changgong_path, pak_path)
    return True, "恢复成功"


def search_pak_file(callback) -> None:
    """在后台线程中全盘搜索 pakchunk90-WindowsClient.pak 文件。

    遍历所有可用盘符，搜索目标文件，每找到一个就通过回调通知。

    Args:
        callback: 回调函数，签名为 callback(event: str, data: str | list)
                  event 为 "found" 时 data 为路径字符串
                  event 为 "done" 时 data 为所有结果列表
                  event 为 "error" 时 data 为错误信息
    """
    def _search():
        results = []
        drives = _get_available_drives()
        callback("status", f"开始搜索 {len(drives)} 个盘符...")

        for drive in drives:
            try:
                for root, dirs, files in os.walk(drive):
                    # 跳过系统目录加速搜索
                    dirs[:] = [
                        d for d in dirs
                        if d not in _SKIP_DIRS and not d.startswith("$")
                    ]
                    if TARGET_PAK in files:
                        full_path = os.path.join(root, TARGET_PAK)
                        results.append(full_path)
                        callback("found", full_path)
            except (OSError, PermissionError):
                continue

        callback("done", results)

    thread = threading.Thread(target=_search, daemon=True)
    thread.start()


def extract_base_path_from_pak(pak_full_path: str) -> str | None:
    """从搜到的 .pak 文件完整路径中提取 Delta Force 基础路径。

    pak 文件路径格式: {base_path}\\DeltaForce\\PackContent\\Paks\\pak-0-2-pakchunk90-WindowsClient.pak
    返回 base_path 部分。

    Args:
        pak_full_path: 搜到的 .pak 文件完整路径

    Returns:
        Delta Force 基础路径，若格式不匹配则返回 None
    """
    marker = os.path.join("DeltaForce", "PackContent", "Paks", TARGET_PAK)
    if marker in pak_full_path:
        return pak_full_path.split(marker)[0].rstrip("\\")
    # 尝试大小写不敏感匹配
    norm_path = pak_full_path.lower()
    norm_marker = marker.lower()
    if norm_marker in norm_path:
        idx = norm_path.index(norm_marker)
        return pak_full_path[:idx].rstrip("\\")
    return None


def _get_available_drives() -> list[str]:
    """获取 Windows 系统上所有可用盘符的根路径"""
    drives = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        path = f"{letter}:\\"
        if os.path.exists(path):
            drives.append(path)
    return drives