import json
import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import gapi

logger = logging.getLogger(__name__)


class GAPIX(ABC):
    @abstractmethod
    def output_file(self) -> Path: ...

    @abstractmethod
    def input_folder(self) -> Path: ...

    @abstractmethod
    def temp_file(self) -> Path: ...

    def remove_redundant_files(self) -> None:
        good_schema_text = self.output_file().read_text()

        # Loop through all of the files while ignoring a specific file each time to make
        # sure each file is necessary to generate the schema.
        input_files = list(self.input_folder().glob("*.json"))
        for i, _ in enumerate(input_files):
            test_files = input_files[:i] + input_files[i + 1 :]
            gapi.generate_from_files(test_files, self.temp_file())
            test_schema_text = self.temp_file().read_text()

            if test_schema_text == good_schema_text:
                logger.info("File %s is redundant", input_files[i].name)
                input_files[i].unlink()
                self.remove_redundant_files()
                return

        self.temp_file().unlink()

    def add_test_file(self, data: dict[str, Any]) -> None:
        """Add a new test file for a given endpoint."""
        # Assume this function will only ever be used for responses.
        new_json_path = self.input_folder() / f"{uuid.uuid4()}.json"
        new_json_path.parent.mkdir(parents=True, exist_ok=True)
        new_json_path.write_text(json.dumps(data, indent=2))

    def generate_schema(self) -> None:
        """Generate a Pydantic schema from test files for a given endpoint."""
        gapi.generate_from_folder(self.input_folder(), self.output_file())
