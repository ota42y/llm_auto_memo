import os
import csv
import glob
import shutil

import easyocr

from common import build_logger, ocr_dir, filterd_dir, get_text_filepath
from rect import merge_nearby_boxes, TextBox
from process import ActiveProsess, FreeActiveProsess


DISTANCE_THRESHOLD = 20
SIZE_THRESHOLD = 5
TEXT_LENGTH_THREASHOLD = 10

logger = build_logger(__name__)

def ocr_file(img_path: str, reader: easyocr.Reader) -> list[TextBox]:
    results = reader.readtext(img_path)

    boxes: list[TextBox] = []
    for r in results:
        # [[np.int32(1), np.int32(1)], [np.int32(2), np.int32(1)], [np.int32(2), np.int32(1)], [np.int32(2), np.int32(2)]]
        x_points = []
        y_points = []
        for p in r[0]:
            x_points.append(int(p[0]))
            y_points.append(int(p[1]))
        x_points.sort()
        y_points.sort()
        boxes.append(TextBox(
            r[1],
            x_points[0],
            y_points[0],
            x_points[-1] - x_points[0],
            y_points[-1] - y_points[0],
        ))

    merges = merge_nearby_boxes(boxes, DISTANCE_THRESHOLD, SIZE_THRESHOLD)
    return [box for box in merges if len(box.text) > TEXT_LENGTH_THREASHOLD]


def ocr_files_in_folder(folder_path: str, reader: easyocr.Reader, active_process: ActiveProsess):
    folder_name = os.path.basename(folder_path)
    os.makedirs(f"{ocr_dir}/{folder_name}", exist_ok=True)

    image_paths = [f for f in glob.glob(f"{folder_path}/*.png") if os.path.isfile(f)]
    image_paths.sort()
    
    for image_path in image_paths:
        if not active_process.is_active():
            break
        if not os.path.isfile(image_path):
            continue

        basename = os.path.splitext(os.path.basename(image_path))[0]
        save_ocr_path = f"{ocr_dir}/{folder_name}/{basename}_ocr.csv"
        save_text_path = f"{ocr_dir}/{folder_name}/{basename}_text.txt"
        if os.path.exists(save_ocr_path) and os.path.exists(save_text_path):
            logger.info(f"already ocr {image_path}")
            continue

        logger.info(f"OCR {image_path}")
        boxes = ocr_file(image_path, reader)
        if not active_process.is_active():
            break
        with open(save_ocr_path, "w") as f:
            writer = csv.writer(f)
            writer.writerow(['x', 'y', 'width', 'height', 'text'])
            for box in boxes:
                writer.writerow([box.x, box.y, box.w, box.h, box.text])

        original_text_path = get_text_filepath(image_path)
        if os.path.exists(original_text_path):
            if not active_process.is_active():
                break
            shutil.copyfile(original_text_path, save_text_path)

def ocr_all(active_process: ActiveProsess):
    logger.info("start ocr all")
    reader = easyocr.Reader(['ja','en'])

    dir_paths =[ d for d in glob.glob(f"{filterd_dir}/*") if os.path.isdir(d)]
    dir_paths.sort()
    for image_path in dir_paths:
        if not active_process.is_active() or active_process.stop_tasks_by_power():
            break
        ocr_files_in_folder(image_path, reader, active_process)


if __name__ == "__main__":
    ocr_all(FreeActiveProsess())

