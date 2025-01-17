import os
from datetime import datetime
from logging import getLogger, StreamHandler, Formatter, Logger

from langchain_openai import ChatOpenAI

images_dir = "./images"
intervals_dir = "./intervals"
filterd_dir = "./filterd"
ocr_dir = "./ocr"
reports_dir = "./reports"

prompt_dir = "templates"
ocr_result_template_path = os.path.join(prompt_dir, "ocr_explanation.txt")
report_template_path = os.path.join(prompt_dir, "report_prompt.txt")

def get_datetime_from_filename(basename: str) -> datetime:
    basename = os.path.splitext(basename)[0]
    return datetime.strptime(basename, "%Y%m%d-%H%M%S")

def get_datetiem_and_display_id(basename: str) -> tuple[datetime, str]:
    basename = os.path.splitext(basename)[0]
    file_splits = basename.split("_")
    file_name = file_splits[0]
    display_id = file_splits[1]

    d = datetime.strptime(file_name, "%Y%m%d-%H%M%S")
    return d, display_id

def build_logger(name: str) -> Logger:
    logger = getLogger(name)
    logger.setLevel("INFO")
    handler = StreamHandler()
    handler.setLevel("INFO")
    handler.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger

def get_text_filepath(img_path: str) -> str:
    basename = os.path.basename(img_path)
    basedir = os.path.dirname(img_path)
    return f"{basedir}/{os.path.splitext(basename)[0]}.txt"


def send_llm(prompt: str, logger: Logger) -> str:
    tempature = 0.3
    while True:
        llm = ChatOpenAI(
            base_url="https://api.platform.preferredai.jp/v1",
            model="plamo-1.0-prime",
            temperature=tempature,
            timeout=60,
        )

        inputs=[
            {"role": "user", "content": prompt},
        ]
        messages = llm.invoke(input=inputs)
        if 4000 < len(messages.content):
            logger.info(f"Too long response {len(messages.content)}")
            tempature += 0.1
            continue
        return messages.content
