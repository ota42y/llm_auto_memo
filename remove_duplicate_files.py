import os
import glob
import shutil

import cv2
import numpy as np

from common import intervals_dir, build_logger, filterd_dir, get_text_filepath
from process import ActiveProsess, FreeActiveProsess

logger = build_logger(__name__)
threashold = 0.001

def load_image_split_by_display_size(parent_dir: str) -> dict[int, list[str]]:
    dispyal_size_to_images: dict[int, list[str]] = {}
    for item in glob.glob(f"{parent_dir}/*.png"):
        if os.path.isfile(item):
            img = cv2.imread(item)
            display_size = img.shape[0] * img.shape[1]
            if display_size not in dispyal_size_to_images:
                dispyal_size_to_images[display_size] = []
            dispyal_size_to_images[display_size].append(item)
    
    for _, images in dispyal_size_to_images.items():
        images.sort()

    return dispyal_size_to_images


def get_diff_image_by_cv2(image1: cv2.typing.MatLike, image2: cv2.typing.MatLike) -> float:
    ab = np.abs(image1 - image2)
    diff= np.sum(ab) * 1.0
    h, w, c = image1.shape
    return diff / (h * w * c * 255)


def check_and_remove_image_by_cv(before_image: cv2.typing.MatLike, images: list[str], active_process: ActiveProsess) -> None:
    for image_path in images:
        if not active_process.is_active():
            break
        logger.info(f"diff check cv2 {image_path}")
        # 画像の差分を計算
        img = cv2.imread(image_path).astype(np.int32)
        if img.shape != before_image.shape:
            logger.info(f"skip: shape is different {img.shape} {before_image.shape}")
            logger.info(f"update before image to {image_path}")
            before_image = img
            continue

        diff = get_diff_image_by_cv2(before_image, img)

        if threashold < diff:
            logger.info(f"skip: diff is {diff}")
            logger.info(f"update before image to {image_path}")
            before_image = img
        else:
            logger.info(f"remove: diff is {diff}")
            text_path = get_text_filepath(image_path)
            if active_process.is_active():
                os.remove(image_path)
                os.remove(text_path)
            


# スリープ状態、口頭で話していた場合などは、画面に変化のないものが存在しうるので削除する
def remove_duplicate_files(active_process: ActiveProsess) -> None:
    dirs = [d for d in glob.glob(f"{intervals_dir}/*") if os.path.isdir(d)]
    dirs.sort()

    already_dir = [d for d in glob.glob(f"{filterd_dir}/*") if os.path.isdir(d)]
    already_dir.sort()
    before_dir = already_dir[-1] if len(already_dir) > 0 else None

    # 現在が10:10分で、08:30から実行されていない場合
    # 08:00 すでに処理済みでfilterd_dirの下にある。before_dirがこれ
    # 08:30 処理対象
    # 09:00 処理対象
    # 09:30 処理対象
    # 10:00 追記されるのでまだ何もできない
    # となるため、最後のディレクトリはskip
    for now_dir in dirs:
        if before_dir is not None:
            before_images = [f for f in glob.glob(f"{before_dir}/*.png") if os.path.isfile(f)]
        else:
            before_images = []

        now_images = [f for f in glob.glob(f"{now_dir}/*.png") if os.path.isfile(f)]
        
        if len(now_images) == 0:
            # なかったら何もしない
            continue

        if len(before_images) == 0:
            temp_img = cv2.imread(now_images[0])
            before_image = np.zeros(temp_img.shape, np.uint8).astype(np.int32)            
        else:
            before_image = cv2.imread(before_images[-1]).astype(np.int32)
        
        check_and_remove_image_by_cv(before_image, now_images, active_process)
        if not active_process.is_active():
            break

        # 差分を計算したので、差分の計算もとである一つ前のディレクトリを移動する
        after_dir = f"{filterd_dir}/{os.path.basename(before_dir)}"
        logger.info(f"check duplitated end so move {before_dir} to {after_dir}")
        if active_process.is_active():
            shutil.move(before_dir, f"{filterd_dir}/{os.path.basename(before_dir)}")
        before_dir = now_dir


if __name__ == "__main__":
    remove_duplicate_files(FreeActiveProsess())
