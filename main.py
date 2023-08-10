import calendar
import config
import cv2
import glob
import json
import os
import pyexcel
import pytesseract
import typer
from datetime import datetime
from enum import Enum
from nanoid import generate as id_generate
from pydantic import BaseModel
from pydantic import ValidationError
from typing import List
from typing_extensions import Annotated

app = typer.Typer()
absolute_path = os.path.dirname(os.path.abspath(__file__))


class TemplateCoordinatesModel(BaseModel):
    x: int
    y: int
    width: int
    height: int
    key: str
    is_number: bool = False


class TemplateModel(BaseModel):
    main: List[TemplateCoordinatesModel]
    second: List[TemplateCoordinatesModel]


class NumberType(Enum):
    even = 0
    odd = 1


class Collector():
    TESSERACT_ARGS_FOR_NUMBER = "--oem 3 --psm 7 digits -c tessedit_char_whitelist=0123456789"
    TESSERACT_ARGS_FOR_TEXT = "--oem 3 --psm 7"

    def __init__(self, template: TemplateModel) -> None:
        self.template = template

        tpl_main = self.template.main and len(self.template.main) > 0
        tpl_second = self.template.second and len(self.template.second) > 0

        if not tpl_main and not tpl_second:
            print(f"Error: template is not conformed")
            return

        # Attention: ID should be in second key of template.json
        idx_id_field = [i for i, e in enumerate(
            self.template.second) if e.key == "id"]
        is_idx = len(idx_id_field) > 0

        if is_idx is True:
            self.template_idx_idkey = idx_id_field[0]
        else:
            print(f"Error: No id field found in template.second")
            return

    def run(self, folder_name: str) -> None:
        # works only for *.jpg or *.png screenshots
        jpg_names = f"./{folder_name}/*.jpg"
        png_names = f"./{folder_name}/*.png"
        files_paths = glob.glob(jpg_names) + glob.glob(png_names)
        if len(files_paths) == 0:
            print(f"Error: Folder is empty")
            return
        if len(files_paths) % 2 != 0:
            print(f"Error: Folder contains no odd number of files")
            return

        paths_sorted = sorted(files_paths)  # sort by file name

        # we need to find if the screenshot at index even or odd contain the id info
        self.idx_screen_id_info = None
        screen_0 = paths_sorted[0]
        print(f"...pre-processing {screen_0}")
        image_0 = cv2.imread(screen_0)
        image_data = self.get_data(image_0, self.template.second)
        supposed_id = image_data[self.template_idx_idkey]
        if supposed_id != "ERROR" and isinstance(supposed_id, int):
            self.idx_screen_id_info = 0
        else:
            screen_01 = paths_sorted[1]
            print(f"...pre-processing {screen_01}")
            image_01 = cv2.imread(screen_01)
            image_data = self.get_data(image_01, self.template.second)
            supposed_id = image_data[self.template_idx_idkey]
            if supposed_id != "ERROR" and isinstance(supposed_id, int):
                self.idx_screen_id_info = 1
        if self.idx_screen_id_info is None:
            print(f"Error: Could not find where is governor ID screenshot")
            return

        id_screen = NumberType.even if self.idx_screen_id_info == 0 else NumberType.odd
        governors = dict()
        current_gov_id = None
        for i, name_path in enumerate(paths_sorted):
            file_path = os.path.join(absolute_path, name_path)
            path_exits = os.path.exists(file_path)
            result = f"{'OK' if path_exits else 'FAILED'}"
            print(f"...reading {file_path}: {result}")
            if not path_exits:
                continue
            image = cv2.imread(file_path)
            print(f"...processing {file_path}: PENDING")

            data = None
            if i % 2 == 0:
                current_gov_id = id_generate()
                if id_screen == NumberType.odd:
                    data = self.get_data(image, self.template.main)
                    governors[current_gov_id] = data
                elif id_screen == NumberType.even:
                    data = self.get_data(image, self.template.second)
                    gov_id = data[self.template_idx_idkey]
                    rest_data = [e for i, e in enumerate(
                        data) if i != self.template_idx_idkey]
                    governors[current_gov_id] = [gov_id] + rest_data
            else:
                if id_screen == NumberType.odd:
                    data = self.get_data(image, self.template.second)
                    if current_gov_id is not None:
                        gov_id = data[self.template_idx_idkey]
                        rest_data = [e for i, e in enumerate(
                            data) if i != self.template_idx_idkey]
                        _old = governors[current_gov_id]
                        governors[current_gov_id] = [gov_id] + _old + rest_data
                elif id_screen == NumberType.even:
                    data = self.get_data(image, self.template.main)
                    if current_gov_id is not None:
                        _old = governors[current_gov_id]
                        governors[current_gov_id] = [_old[0]] + data + _old[1:]

        self.save_data(governors.values())

    def get_data(self, image, locations: List[TemplateCoordinatesModel]) -> List[str]:
        """ For an image, locations refer to all possible data we want to extract.
        Return a list of values extracted from provided locations.
        """
        values = []
        for location in locations:
            # use coordinates above to select the desired area
            cropped_image = image[
                location.y:location.y + location.height,
                location.x:location.x + location.width
            ]

            # image in gray scale mode, easier to extract data
            gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

            # if the data we want to extract is a number or a string
            data_type_number = location.is_number is True
            if data_type_number:
                tess_cfg = Collector.TESSERACT_ARGS_FOR_NUMBER
            else:
                tess_cfg = Collector.TESSERACT_ARGS_FOR_TEXT

            result = pytesseract.image_to_string(gray_image, config=tess_cfg)

            # if the result is an empty value, we skip it
            text_result = result.strip().replace("\n", "")
            if text_result == "":
                values += ["ERROR"]
                continue

            # if data is a number, we cast the value to an integer
            if data_type_number:
                try:
                    text_result = int(text_result)
                except Exception as e:
                    text_result = "ERROR"
                    print(e)

            values += [text_result]
        return values

    def save_data(self, data):
        headers = ["id"] + \
            [e.key for e in self.template.main] + \
            [e.key for i, e in enumerate(
                self.template.second) if i != self.template_idx_idkey]

        export_content = []
        export_content.append(headers)
        export_content += data

        d_now = datetime.utcnow()
        date = d_now.strftime('%d_%m_%Y')
        ts = calendar.timegm(d_now.timetuple())
        filename = "%s-%s" % (date, ts)
        file_destination = os.path.abspath("./%s.xlsx" % (filename))

        # Save data into an .xlsx file
        pyexcel.save_as(array=export_content, dest_file_name=file_destination)


@app.command()
def hello():
    print(f"=== {config.APP_NAME}: version {config.APP_VERSION} ===")


@app.command()
def collect(
    template: Annotated[str, typer.Option("--using")],
    folder: Annotated[str, typer.Option("--from-folder")]
):
    hello()

    file_path = os.path.join(absolute_path, template)
    json_data = None

    try:
        with open(file_path) as json_file:
            json_data = json.load(json_file)
    except Exception as e:
        print(e)

    if json_data is None:
        print(f"Could not read the template configuration from {template}")
        return

    try:
        data = TemplateModel(**json_data)
    except ValidationError as e:
        print(e)
        return

    collector = Collector(data)
    collector.run(folder)


if __name__ == "__main__":
    app()
