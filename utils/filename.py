from pathlib import Path


def create_output_pdf_path(
    zip_path: Path,
    output_dir: Path
) -> Path:
    """
    出力PDFのパスを生成する

    sample.zip
    → sample_結合.pdf
    """

    return (
        output_dir /
        f"{zip_path.stem}_結合.pdf"
    )


def create_log_path(
    zip_path: Path,
    output_dir: Path
) -> Path:
    """
    ログファイルのパスを生成する

    sample.zip
    → sample_エラー.log
    """

    return (
        output_dir /
        f"{zip_path.stem}_エラー.log"
    )