import os
import sys
import time

from common import build_logger, ocr_result_template_path, report_template_path
from process import ActiveProsessByFile, ACTIVE_PROCESS_FILE_PATH
from move_images import move_images, remove_empty_folders
from image_to_text import ocr_all
from remove_duplicate_files import remove_duplicate_files
from create_explanation import create_explanation
from create_report import create_reports
from move_archive_folder import move_achive_folder

logger = build_logger(__name__)


"""
一定時間ごとにスクリーンショットがimagesに保存される
保存した時間を30分ごとに分割し、intervalsに移動する
直前のスクリーンショットと一定以上差分があったものだけfilterdに移動し、それ以外は消す
filterdに保存されたものをOCRを使って画像からテキストを取得し、ocrに保存する
ocrに保存されたテキストを使って、LLMにその時何をしているかを説明させる
時間枠ごとの説明を合わせて、その時間に何をしていたかをまとめる
"""
if __name__ == "__main__":
    # 引数に --force があったらバッテリーの充電状態に関係なく実行する
    # 引数に --force がない場合はバッテリーの充電状態を確認して、充電されている時だけ実行する

    args = sys.argv
    if "--force" in args:
        logger.info("force so do heavy tasks")
        force = True
    else:
        force = False
    
    if not os.path.exists(ocr_result_template_path):
        logger.info(f"not found {ocr_result_template_path}")
        sys.exit(1)
    if not os.path.exists(report_template_path):
        logger.info(f"not found {report_template_path}")
        sys.exit(1)

    active_process = ActiveProsessByFile(
        active_file_path=ACTIVE_PROCESS_FILE_PATH,
        force_plugged=force,
    )
    active_process.active()
    time.sleep(1)

    move_images(active_process)
    remove_empty_folders(active_process)
    remove_duplicate_files(active_process)    

    ocr_all(active_process)
    create_explanation(active_process)
    create_reports(active_process)
    move_achive_folder(active_process)

    logger.info("finish")
