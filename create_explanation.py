import os
import csv
import glob
import queue
import string
import threading

from common import ocr_dir, build_logger, send_llm, ocr_result_template_path
from process import ActiveProsess, FreeActiveProsess

logger = build_logger(__name__)

LLM_THREAD_NUM = 3

class OCRResult:
    def __init__(self, ocr_csv_path: str):
        self.ocr_result_path = ocr_csv_path
        self.folder = os.path.basename(os.path.dirname(ocr_csv_path))

        basename = os.path.basename(ocr_csv_path)
        datetime_name = basename.replace("_ocr.csv", "")
        self.datetime_name = datetime_name

        self.text_path = os.path.join(
            os.path.dirname(ocr_csv_path),
            f"{datetime_name}_text.txt",
        )

    def is_valid(self) -> bool:
        # windowがなくても最悪OK
        return os.path.exists(self.ocr_result_path)

    # csv_pathを辞書順でソートできるようにする
    def __lt__(self, other: "OCRResult") -> bool:
        return self.ocr_result_path < other.ocr_result_path
    
    def prompt_path(self) -> str:
        return f"{ocr_dir}/{self.folder}/{self.datetime_name}_prompt.txt"

    def explanation_path(self) -> str:
        return f"{ocr_dir}/{self.folder}/{self.datetime_name}_explanation.txt"


def load_ocrs() -> list[OCRResult]:
    results: list[OCRResult] = []
    for item in glob.glob(f"{ocr_dir}/**/*_ocr.csv", recursive=True):
        if not os.path.isfile(item):
            continue

        result = OCRResult(item)
        if result.is_valid():
            results.append(result)

    results.sort()
    return results


def add_ocr_results_to_queue(q: 'queue.Queue[OCRResult]') -> None:
    ocr_results = load_ocrs()
    for ocr_result in ocr_results:
        q.put(ocr_result)

def load_and_build_prompt(ocr_result: OCRResult, prompt_template: string.Template) -> str:
    texts: list[str] = []
    with open(ocr_result.ocr_result_path) as f:
        reader = csv.reader(f)
        for row in reader:
            if 4 <= len(row):
                texts.append(row[4])
        
    window, title = "", ""
    if os.path.exists(ocr_result.text_path):
        text_content = open(ocr_result.text_path).read()
        splitted = text_content.split(",",maxsplit=1)
        if 2 <= len(splitted):
            window, title = splitted

    return prompt_template.safe_substitute(
        datetime_str=ocr_result.datetime_name,
        application_name=window,
        window_title=title,
        ocr_text="\n".join(texts),
    )


def llm_worker(q: 'queue.Queue[OCRResult]', active_process: ActiveProsess, index: int) -> None:
    with open(ocr_result_template_path) as f:
        prompt_template = string.Template(f.read())

    while True:
        if not active_process.is_active() or active_process.stop_tasks_by_power():
            break
        try:
            ocr_result = q.get(block=False)
        except queue.Empty:
            break

        if os.path.exists(ocr_result.explanation_path()):
            logger.info(f"{index}: Already processed {ocr_result.explanation_path()}")
            continue

        logger.info(f"{index}: build prompt {ocr_result.prompt_path()}")
        prompt = load_and_build_prompt(ocr_result, prompt_template)
        if not active_process.is_active():
            break
        with open(ocr_result.prompt_path(), "w") as f:
            f.write(prompt)

        result = send_llm(prompt=prompt, logger=logger)
        logger.info(f"{index}: save result to {ocr_result.explanation_path()}")
        if not active_process.is_active():
            break
        with open(ocr_result.explanation_path(), "w") as f:
            f.write(result)


def create_explanation(active_process: ActiveProsess) -> None:
    logger.info("start create explanation")
    q: 'queue.Queue[OCRResult]' = queue.Queue()

    ocr_results = load_ocrs()
    for ocr_result in ocr_results:
        q.put(ocr_result)

    llms: list[threading.Thread] = [threading.Thread(target=llm_worker, args=(q, active_process, i,)) for i in range(LLM_THREAD_NUM)]
    [llm.start() for llm in llms]
    [llm.join() for llm in llms]


if __name__ == "__main__":
    create_explanation(FreeActiveProsess())

