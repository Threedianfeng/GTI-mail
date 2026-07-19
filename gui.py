"""GUI 界面模块 - 使用 tkinter 实现"""

import os
import tkinter as tk
from tkinter import filedialog
import file_ops


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("三角洲行动 - 文件改名工具")
        self.root.geometry("600x520")
        self.root.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        # --- 根目录选择区域 ---
        dir_frame = tk.Frame(self.root)
        dir_frame.pack(pady=(15, 5), padx=15, fill=tk.X)

        tk.Label(dir_frame, text="根目录:", font=("", 10)).pack(side=tk.LEFT)

        self.dir_entry = tk.Entry(dir_frame, width=42)
        self.dir_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(dir_frame, text="浏览...", command=self._browse_dir).pack(side=tk.LEFT)

        # --- 搜索按钮 ---
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=(0, 5), padx=15, fill=tk.X)

        self.search_btn = tk.Button(
            search_frame,
            text="搜索文件 (全盘搜索 pakchunk90-WindowsClient.pak)",
            font=("", 10),
            command=self._on_search,
        )
        self.search_btn.pack(side=tk.LEFT)

        self.search_status = tk.Label(search_frame, text="", font=("", 9), fg="gray")
        self.search_status.pack(side=tk.LEFT, padx=10)

        # --- 操作按钮区域 ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame,
            text="已经进入长工并退出游戏",
            font=("", 11),
            width=24,
            height=2,
            command=self._on_rename,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="已经退出游戏",
            font=("", 11),
            width=16,
            height=2,
            command=self._on_restore,
        ).pack(side=tk.LEFT, padx=10)

        # --- 操作日志区域 ---
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=(5, 5), padx=15, fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="操作日志:", font=("", 10)).pack(anchor=tk.W)

        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # --- 制作者声明 ---
        tk.Label(
            self.root,
            text="本脚本由三点进场刮大风制作，完全免费，所有收费的都是骗子",
            font=("", 10, "bold"),
            fg="#CC3333",
        ).pack(pady=(0, 10))

    # --- 事件处理 ---

    def _browse_dir(self):
        path = filedialog.askdirectory(title="选择游戏根目录")
        if path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, path)

    def _get_root_dir(self) -> str | None:
        path = self.dir_entry.get().strip()
        if not path:
            self._log("错误: 请先选择根目录")
            return None
        return path

    def _find_base_path(self, root_dir: str) -> str | None:
        """查找 Delta Force 目标文件夹。

        优先检查根目录的上一级是否就是 Delta Force 文件夹，
        若是则直接使用；否则递归向下查找。
        """
        # 1. 先检查上级目录
        parent = file_ops.find_delta_force_parent(root_dir)
        if parent:
            self._log(f"上级目录已是 Delta Force: {parent}")
            return parent

        # 2. 向下递归查找
        return file_ops.find_deepest_delta_force(root_dir)

    def _on_rename(self):
        root_dir = self._get_root_dir()
        if root_dir is None:
            return

        base_path = self._find_base_path(root_dir)
        if base_path is None:
            self._log("错误: 未找到 Delta Force 文件夹")
            return

        self._log(f"找到目标文件夹: {base_path}")
        success, msg = file_ops.rename_to_changgong(base_path)
        self._log(msg)

    def _on_restore(self):
        root_dir = self._get_root_dir()
        if root_dir is None:
            return

        base_path = self._find_base_path(root_dir)
        if base_path is None:
            self._log("错误: 未找到 Delta Force 文件夹")
            return

        self._log(f"找到目标文件夹: {base_path}")
        success, msg = file_ops.restore_from_changgong(base_path)
        self._log(msg)

    def _on_search(self):
        """全盘搜索目标 .pak 文件"""
        self.search_btn.configure(state=tk.DISABLED)
        self.search_status.configure(text="搜索中，请稍候...")
        self._log("========== 开始全盘搜索 pakchunk90-WindowsClient.pak ==========")

        def on_callback(event: str, data):
            self.root.after(0, lambda: self._handle_search_result(event, data))

        file_ops.search_pak_file(on_callback)

    def _handle_search_result(self, event: str, data):
        if event == "status":
            self.search_status.configure(text=data)
        elif event == "found":
            self._log(f"找到: {data}")
        elif event == "done":
            count = len(data) if isinstance(data, list) else 0
            if count == 0:
                self._log("搜索完成: 未找到任何匹配文件")
            elif count == 1:
                self._log(f"搜索完成: 找到 1 个文件")
                # 自动提取并填充到根目录
                base_path = file_ops.extract_base_path_from_pak(data[0])
                if base_path:
                    self.dir_entry.delete(0, tk.END)
                    self.dir_entry.insert(0, base_path)
                    self._log(f"已自动填充根目录: {base_path}")
            else:
                self._log(f"搜索完成: 共找到 {count} 个文件，请手动选择其中一个")
                self._log("提示: 多个结果说明电脑中有多个游戏副本，请手动复制路径到根目录输入框")
            self.search_btn.configure(state=tk.NORMAL)
            self.search_status.configure(text=f"搜索完成，共 {count} 个结果")
        elif event == "error":
            self._log(f"搜索出错: {data}")
            self.search_btn.configure(state=tk.NORMAL)
            self.search_status.configure(text="")

    def _log(self, message: str):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()