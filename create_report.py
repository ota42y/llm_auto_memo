import os
import glob
import string
import queue
import threading

from common import ocr_dir, build_logger, send_llm, reports_dir, report_template_path
from process import ActiveProsess, FreeActiveProsess

logger = build_logger(__name__)

LLM_THREAD_NUM = 3

def load_explanations(folder_path: str) -> dict[str, str]:
    explanations = {}
    for item in glob.glob(f"{folder_path}/*_explanation.txt"):
        if not os.path.isfile(item):
            continue
        
        datetime_name = os.path.basename(item).replace("_explanation.txt", "")
        content = open(item).read()

        explanations[datetime_name] = content
    return explanations

def build_prompt(explanations: dict[str, str]) -> str:
    keys = list(explanations.keys())
    keys.sort()

    with open(report_template_path) as f:
        prompt_template = string.Template(f.read())

    ocr_results = ""
    for key in keys:
        ocr_results += f"----\n"
        ocr_results += f"datetime: {key}\n\n"
        ocr_results += explanations[key] + "\n"
    return prompt_template.safe_substitute(ocr_results=ocr_results)

def create_report(folder_path: str, active_process: ActiveProsess) -> None:
    folder_name = os.path.basename(folder_path)
    save_path = f"{reports_dir}/{folder_name}_report.txt"
    if os.path.exists(save_path):
        logger.info(f"skip create report for {folder_path}")
        return
    
    logger.info(f"start create report for {folder_path}")
    explanations = load_explanations(folder_path)
    prompt = build_prompt(explanations)
    if prompt == "":
        logger.info(f"skip create report for {folder_path} because no explanations")
        return

    prompt_path = f"{reports_dir}/{folder_name}_prompt.txt"
    if not active_process.is_active():
        return
    with open(prompt_path, "w") as f:
        f.write(prompt)

    result = send_llm(prompt=prompt, logger=logger)
    logger.info(f"save report for {folder_path} to {save_path}")
    if not active_process.is_active():
        return
    with open(save_path, "w") as f:
        f.write(result)


def report_worker(q: 'queue.Queue[str]', active_process: ActiveProsess) -> None:
    while True:
        if not active_process.is_active() or active_process.stop_tasks_by_power():
            logger.info("stop report worker")
            return
        try:
            logger.info("load from queue")
            folder_path = q.get(block=False)
        except queue.Empty:
            return
        create_report(folder_path, active_process)


def create_reports(active_process: ActiveProsess) -> None:
    logger.info("start create reports")
    q: 'queue.Queue[str]' = queue.Queue()

    for folder_path in glob.glob(f"{ocr_dir}/*"):
        if not os.path.isdir(folder_path):
            continue
        q.put(folder_path)

    llms: list[threading.Thread] = [threading.Thread(target=report_worker, args=(q, active_process, )) for _ in range(LLM_THREAD_NUM)]
    [llm.start() for llm in llms]
    [llm.join() for llm in llms]


if __name__ == "__main__":
    create_reports(FreeActiveProsess())

