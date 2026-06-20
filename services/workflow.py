# services/workflow.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from pypdf import PdfReader

from models.student import Student
from models.submission_file import SubmissionFile
from services.file_detector import FileDetector, FileType
from services.image_to_pdf import ImageToPdfConverter
from services.logger import Logger
from services.pdf_merger import PdfMerger
from services.pdf_processor import PdfProcessor
from services.zip_reader import ZipReader
from utils.filename import create_log_path, create_output_pdf_path
from utils.student_id import extract_student_id


ProgressCallback = Callable[[int, int], None]
LogCallback = Callable[[str], None]


@dataclass
class WorkflowResult:
    success: bool
    output_pdf_path: Path
    log_path: Path
    total_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0


class Workflow:
    def __init__(
        self,
        progress_callback: ProgressCallback | None = None,
        log_callback: LogCallback | None = None,
        logger: Logger | None = None,
    ):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.logger = logger if logger is not None else Logger()

    def process(self, zip_path: Path, output_dir: Path = Path("output")) -> WorkflowResult:
        zip_path = Path(zip_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_pdf_path = create_output_pdf_path(zip_path, output_dir)
        log_path = create_log_path(zip_path, output_dir)

        self.logger.clear()
        self._log("info", f"処理開始: {zip_path.name}")

        reader = ZipReader(zip_path)

        total_files = 0
        processed_files = 0
        skipped_files = 0
        labeled_pdfs: list[Path] = []

        try:
            root = reader.extract()
            all_files = reader.get_all_files()

            students = self._collect_students(root, all_files)
            total_files = sum(len(student.files) for student in students)

            if total_files == 0:
                self._log("warning", "有効な提出ファイルが見つかりませんでした")
                return WorkflowResult(
                    success=False,
                    output_pdf_path=output_pdf_path,
                    log_path=log_path,
                    total_files=0,
                    processed_files=0,
                    skipped_files=0,
                )

            with TemporaryDirectory() as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                current = 0

                for student in students:
                    student_total_pages = 0
                    for submission_file in student.files:
                        file_type = FileDetector.detect(submission_file.path)
                        if file_type == FileType.PDF:
                            if not self._is_valid_pdf(
                                submission_file.path
                            ):
                                continue

                            pdf_reader = PdfReader(
                                str(submission_file.path)
                            )

                            student_total_pages += len(
                                pdf_reader.pages
                            )
                        elif file_type == FileType.IMAGE:
                            student_total_pages += 1
                    
                    current_page = 1

                    self._log(
                        "info",
                        f"{student.student_id}: "
                        f"{student_total_pages}ページ"
                    )

                    for submission_file in student.files:
                        current += 1
                        self._progress(current, total_files)
                        self._log("info", f"{student.student_id}: {submission_file.path.name}")

                        try:
                            file_type = FileDetector.detect(submission_file.path)

                            if file_type == FileType.PDF:
                                if not self._is_valid_pdf(submission_file.path):
                                    raise ValueError("PDFとして読み込めない")

                                pdf_source = temp_dir / f"source_{current}.pdf"
                                pdf_source.write_bytes(submission_file.path.read_bytes())

                            elif file_type == FileType.IMAGE:
                                pdf_source = temp_dir / f"source_{current}.pdf"
                                ImageToPdfConverter.convert(submission_file.path, pdf_source)
                                self._log("info", f"画像をPDFに変換: {submission_file.path.name} -> {pdf_source.name}")

                            else:
                                skipped_files += 1
                                self._log("warning", f"対象外のため無視: {submission_file.path.name}")
                                continue

                            labeled_path = temp_dir / f"labeled_{current}.pdf"

                            PdfProcessor.add_label(
                                pdf_source,
                                labeled_path,
                                student.student_id,
                                current_page,
                                student_total_pages,
                            )

                            pdf_reader = PdfReader(
                                str(pdf_source)
                            )

                            page_count = len(
                                pdf_reader.pages
                            )

                            current_page += page_count

                            labeled_pdfs.append(labeled_path)
                            processed_files += 1

                        except Exception as exc:
                            skipped_files += 1
                            self._log("error", f"{submission_file.path.name} の処理に失敗: {exc}")

                if not labeled_pdfs:
                    self._log("error", "結合可能なPDFが1件もありませんでした")
                    return WorkflowResult(
                        success=False,
                        output_pdf_path=output_pdf_path,
                        log_path=log_path,
                        total_files=total_files,
                        processed_files=processed_files,
                        skipped_files=skipped_files,
                    )

                PdfMerger.merge(labeled_pdfs, output_pdf_path)
                self._log("info", f"出力完了: {output_pdf_path.name}")

                return WorkflowResult(
                    success=True,
                    output_pdf_path=output_pdf_path,
                    log_path=log_path,
                    total_files=total_files,
                    processed_files=processed_files,
                    skipped_files=skipped_files,
                )

        except Exception as exc:
            self._log("error", f"致命的なエラー: {exc}")
            return WorkflowResult(
                success=False,
                output_pdf_path=output_pdf_path,
                log_path=log_path,
                total_files=total_files,
                processed_files=processed_files,
                skipped_files=skipped_files,
            )

        finally:
            reader.cleanup()
            try:
                self.logger.save(log_path)
            except Exception as exc:
                if self.log_callback:
                    self.log_callback(f"[ERROR] ログ保存に失敗: {exc}")

    def _collect_students(self, root: Path, files: list[Path]) -> list[Student]:
        students: dict[str, Student] = {}

        for file_path in files:
            student_id = self._find_student_id(root, file_path)

            if student_id is None:
                self._log("warning", f"学生番号を取得できないため無視: {file_path.name}")
                continue

            student = students.setdefault(student_id, Student(student_id))
            student.add_file(SubmissionFile(path=file_path))

        result = list(students.values())

        for student in result:
            student.sort_files()

        result.sort(key=lambda s: s.student_id)
        return result

    def _find_student_id(self, root: Path, file_path: Path) -> str | None:
        try:
            relative_parts = file_path.relative_to(root).parts
        except Exception:
            relative_parts = file_path.parts

        for part in relative_parts:
            student_id = extract_student_id(part)
            if student_id is not None:
                return student_id

        return None

    def _is_valid_pdf(self, pdf_path: Path) -> bool:
        try:
            PdfReader(str(pdf_path))
            return True
        except Exception:
            return False

    def _progress(self, current: int, total: int):
        if self.progress_callback is not None:
            self.progress_callback(current, total)

    def _log(self, level: str, message: str):
        level = level.lower()

        if level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)

        if self.log_callback is not None:
            messages = self.logger.get_messages()
            if messages:
                self.log_callback(messages[-1])