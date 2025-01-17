import os
import uuid
import abc

import psutil

from common import build_logger

logger = build_logger(__name__)

ACTIVE_PROCESS_FILE_PATH = "active_process.txt"

class ActiveProsess(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def is_active(self) -> bool:
        pass

    @abc.abstractmethod
    def stop_tasks_by_power(self) -> bool:
        pass

# 同時に複数のプロセスが実行されないよう、誰がアクティブかを管理する
# active_prosessにかかれているものと同じIDを持っていれば自分がアクティブ
# 他のプロセスが実行したい場合は、active_prosessを上書きする
# 実行前にactive_prosessを確認して、IDが書き換わっていたらファイル操作などをせずに終了する
class ActiveProsessByFile(ActiveProsess):
    def __init__(self, active_file_path: str, force_plugged: bool) -> None:
        self.process_id = str(uuid.uuid4())
        self.active_file_path = active_file_path
        self.force_plugged = force_plugged
        self.stopped = False

    def active(self) -> None:
        logger.info(f"active process: {self.process_id}")
        with open(self.active_file_path, "w") as f:
            f.write(self.process_id)

    def is_active(self) -> bool:
        if not os.path.exists(self.active_file_path):
            return False
        with open(self.active_file_path, "r") as f:
            process_id = f.read()
        return process_id == self.process_id    


    def stop_tasks_by_power(self) -> bool:
        if self.force_plugged:
            return False

        if self.stopped:
            return True

        # 一度でもstopしたら以降ずっとstopして終了させる        
        if not psutil.sensors_battery().power_plugged:
            self.stopped = True
            return True
        return False


class FreeActiveProsess(ActiveProsess):
    def is_active(self) -> bool:
        return True

    def stop_tasks_by_power(self) -> bool:
        return True