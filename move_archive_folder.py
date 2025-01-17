import os
import glob
import datetime
import re
import shutil

from common import build_logger, reports_dir, ocr_dir, filterd_dir
from process import ActiveProsess, FreeActiveProsess

LATEST_ADDED_PREFIX = "report_added: "

logger = build_logger(__name__)

def build_archive_path(archive_dir: str, dt: datetime.datetime) -> str:
    archive_dir = f"{archive_dir}/{dt.strftime('%Y')}/{dt.strftime('%Y-%m')}"
    archive_file = f"{dt.strftime('%Y-%m-%d')}-report.md"
    return os.path.join(archive_dir, archive_file)


def get_latest_added_name(archive_path: str, date_str: str) -> list[datetime.datetime]:
    if not os.path.isfile(archive_path):
        with open(archive_path, "w") as f:
            f.write(f"${date_str}\n")
        return []

    addeds: list[datetime.datetime] = []
    lines = open(archive_path).read().splitlines()
    for line in lines:        
        m = re.search(r' *' + re.escape(LATEST_ADDED_PREFIX) + r'(\d+-\d+)', line)
        if m is None:
            continue
        dt = datetime.datetime.strptime(m.groups()[0], "%Y%m%d-%H%M%S")
        addeds.append(dt)
    
    return addeds

def add_report_to_file(file_path: str, achive_dir: str, active_process: ActiveProsess) -> None:
    logger.info(f"add report to file: {file_path}")

    basename = os.path.basename(file_path)
    datetime_str = basename.replace("_report.txt", "")
    dt = datetime.datetime.strptime(datetime_str, "%Y%m%d-%H%M%S")
    archive_path = build_archive_path(achive_dir, dt)

    addeds = get_latest_added_name(archive_path, dt.strftime("%Y-%m-%d"))
    latest = max(addeds) if len(addeds) > 0 else datetime.datetime(2000, 1, 1)
    if dt <= latest:
        logger.info(f"skip: {dt} <= {latest}")
        return
    
    logger.info(f"add to {archive_path} from {file_path}")
    report_content = open(file_path).read()
    if not active_process.is_active():
        return
    with open(archive_path, "a") as f:
        f.write("\n")
        f.write("```")
        f.write(f"\n{LATEST_ADDED_PREFIX}{dt.strftime('%Y%m%d-%H%M%S')}\n")
        f.write(report_content)
        f.write("\n")
        f.write("```")
        f.write("\n")


def remove_files(report_file_path: str, active_process: ActiveProsess) -> None:
    basename = os.path.basename(report_file_path)
    datetime_str = basename.replace("_report.txt", "")
    dt = datetime.datetime.strptime(datetime_str, "%Y%m%d-%H%M%S")
    now = datetime.datetime.now()
    if now - dt < datetime.timedelta(days=1):
        logger.info(f"skip remove files: {report_file_path}")
        return

    remove_paths = [report_file_path]

    basename = os.path.basename(report_file_path)
    datetime_str = basename.replace("_report.txt", "")
    if datetime_str == "":
        logger.error(f"invalid file name: {report_file_path}")
        return
    remove_paths.append(os.path.join(reports_dir, f"{datetime_str}_prompt.txt"))
    remove_paths.append(os.path.join(ocr_dir, datetime_str))
    remove_paths.append(os.path.join(filterd_dir, datetime_str))
    for path in remove_paths:
        if not active_process.is_active():
            return
        if os.path.isfile(path):
            logger.info(f"remove file: {path}")
            os.remove(path)
        else:
            logger.info(f"remove dir: {path}")
            shutil.rmtree(path)


def move_achive_folder(active_process: ActiveProsess):
    logger.info("start move archive folder")
    archive_dir = os.environ.get("WORK_REPORT_ARCHIVE_PATH")
    if archive_dir is None:
        raise ValueError("WORK_REPORT_ARCHIVE_PATH is not set")
    
    for file_path in glob.glob(f"{reports_dir}/*_report.txt"):
        if not active_process.is_active() or active_process.stop_tasks_by_power():
            logger.info("stop move archive folder")
            break
        if not os.path.isfile(file_path):
            continue
        add_report_to_file(file_path, archive_dir, active_process)
        remove_files(file_path, active_process)


if __name__ == "__main__":
    move_achive_folder(FreeActiveProsess())
