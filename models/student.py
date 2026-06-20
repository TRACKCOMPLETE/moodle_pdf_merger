from dataclasses import dataclass, field

from models.submission_file import SubmissionFile


@dataclass
class Student:
    student_id: str
    files: list[SubmissionFile] = field(default_factory=list)

    def add_file(self, submission_file: SubmissionFile):
        self.files.append(submission_file)

    def sort_files(self):
        self.files.sort(
            key=lambda f: f.path.name.lower()
        )

        total = len(self.files)

        for index, file in enumerate(
            self.files,
            start=1
        ):
            file.index = index
            file.total = total