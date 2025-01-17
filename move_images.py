import os
import glob
import shutil

from common import get_datetime_from_filename, intervals_dir, images_dir
from process import ActiveProsess, FreeActiveProsess

def move_images(active_process: ActiveProsess) -> None:
    for image_path in glob.glob(f"./{images_dir}/**/*", recursive=True):
        if not os.path.isfile(image_path):
            continue

        basename = os.path.basename(image_path)
        dt = get_datetime_from_filename(basename)
        # 30分の枠ごとに切り詰める
        if dt.minute >= 30:
            dt = dt.replace(minute=30, second=0)
        else:
            dt = dt.replace(minute=0, second=0)

        key = dt.strftime("%Y%m%d-%H%M%S")
        save_dir = f"{intervals_dir}/{key}"
        if active_process.is_active():
            os.makedirs(save_dir, exist_ok=True)
            shutil.move(image_path, f"{save_dir}/{basename}")        

def remove_empty_folders(active_process: ActiveProsess) -> None:
    dirs = [d for d in glob.glob(f"{images_dir}/*") if os.path.isdir(d)]
    dirs.sort()
    
    # 最後のディレクトリは追加される可能性があるので消さない
    for d in dirs[:-1]:
        if not os.listdir(d):
            if active_process.is_active():
                os.rmdir(d)

if __name__ == "__main__":
    move_images(FreeActiveProsess())
    remove_empty_folders(FreeActiveProsess())
