# gui/main_window.py

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path

from tkinterdnd2 import TkinterDnD

from gui.drag_drop import DragDropHandler
from services.workflow import Workflow


class MainWindow:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("Moodle PDF Merger")
        self.root.geometry("900x650")
        self.root.minsize(780, 560)

        self._processing = False
        self._drop_message = "ZIPファイルをここへドラッグ＆ドロップ"
        self._status_text = tk.StringVar(value="待機中")

        self._build_ui()

    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=3)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=2)
        self.root.grid_columnconfigure(0, weight=1)

        drop_frame = tk.Frame(self.root)
        drop_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        drop_frame.grid_rowconfigure(0, weight=1)
        drop_frame.grid_columnconfigure(0, weight=1)

        self.drop_area = tk.Canvas(
            drop_frame,
            highlightthickness=0,
            bg=self.root.cget("bg"),
            cursor="hand2",
        )
        self.drop_area.grid(row=0, column=0, sticky="nsew")
        self.drop_area.bind("<Configure>", self._on_drop_area_resize)

        DragDropHandler(self.drop_area, self._on_zip_dropped)

        status_frame = tk.Frame(self.root)
        status_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        status_frame.grid_columnconfigure(0, weight=1)

        status_label = tk.Label(status_frame, textvariable=self._status_text, anchor="w")
        status_label.grid(row=0, column=0, sticky="ew")

        log_frame = tk.Frame(self.root)
        log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            state="disabled",
            height=10,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self._redraw_drop_area()

    def _on_drop_area_resize(self, event):
        self._redraw_drop_area()

    def _redraw_drop_area(self):
        self.drop_area.delete("all")

        width = max(1, self.drop_area.winfo_width())
        height = max(1, self.drop_area.winfo_height())

        margin = 20
        radius = 30

        x1 = margin
        y1 = margin
        x2 = width - margin
        y2 = height - margin

        self._create_rounded_rect(
            self.drop_area,
            x1,
            y1,
            x2,
            y2,
            radius,
            fill="#f7f7f7",
            outline="#8a8a8a",
            width=2,
        )

        self.drop_area.create_text(
            width // 2,
            height // 2 - 14,
            text=self._drop_message,
            font=("TkDefaultFont", 16, "bold"),
            fill="#222222",
        )

        self.drop_area.create_text(
            width // 2,
            height // 2 + 18,
            text="ここに ZIP を落としてや",
            font=("TkDefaultFont", 11),
            fill="#555555",
        )

    def _create_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=36,
            **kwargs,
        )

    def _on_zip_dropped(self, zip_path):
        zip_path = Path(zip_path)

        if zip_path.suffix.lower() != ".zip":
            self.log(f"[WARNING] ZIP以外は無視: {zip_path.name}")
            return

        if self._processing:
            self.log("[WARNING] いま処理中やから、終わるまで待ってな")
            return

        self._processing = True
        self._set_status(f"処理開始: {zip_path.name}")
        self._set_drop_message("処理中...")
        self.log(f"[INFO] 受け取り: {zip_path}")

        thread = threading.Thread(
            target=self._process_zip_worker,
            args=(zip_path,),
            daemon=True,
        )
        thread.start()

    def _process_zip_worker(self, zip_path: Path):
        try:
            workflow = Workflow(
                progress_callback=self._on_progress,
                log_callback=self._on_workflow_log,
            )
            result = workflow.process(zip_path, Path("output"))
            self.root.after(0, self._on_process_finished, result)
        except Exception as exc:
            self.root.after(0, self.log, f"[ERROR] ワークフロー実行中に例外: {exc}")
            self.root.after(0, self._finish_processing, False, None)

    def _on_progress(self, current: int, total: int):
        self.root.after(0, self._set_status, f"処理中: {current} / {total}")

    def _on_workflow_log(self, message: str):
        self.root.after(0, self.log, message)

    def _on_process_finished(self, result):
        if result.success:
            self.log(f"[INFO] 結合完了: {result.output_pdf_path}")
            self.log(f"[INFO] ログ保存: {result.log_path}")
            self._set_status(
                f"完了: {result.processed_files}件処理 / {result.skipped_files}件スキップ"
            )
            self._set_drop_message("ZIPファイルをここへドラッグ＆ドロップ")
        else:
            self.log("[ERROR] 処理は完了したけど、出力できへんかった")
            self._set_status("失敗")
            self._set_drop_message("ZIPファイルをここへドラッグ＆ドロップ")

        self._processing = False
        self._redraw_drop_area()

    def _finish_processing(self, success: bool, message: str | None):
        self._processing = False
        self._set_drop_message("ZIPファイルをここへドラッグ＆ドロップ")
        self._redraw_drop_area()

        if success:
            self._set_status("完了")
        else:
            self._set_status("失敗")

        if message:
            self.log(message)

    def _set_drop_message(self, message: str):
        self._drop_message = message
        self._redraw_drop_area()

    def _set_status(self, message: str):
        self._status_text.set(message)

    def log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def run(self):
        self.root.mainloop()