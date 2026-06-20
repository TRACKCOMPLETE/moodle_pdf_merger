import re


STUDENT_ID_PATTERN = re.compile(
    r"([BC]\d{6})"
)


def extract_student_id(
    folder_name: str
) -> str | None:
    """
    Moodleのフォルダ名から学生番号を抽出する

    例:
        B123456_山田太郎_assignsubmission_file_
        → B123456

        C654321
        → C654321

        hoge
        → None
    """

    match = STUDENT_ID_PATTERN.search(
        folder_name
    )

    if match is None:
        return None

    return match.group(1)