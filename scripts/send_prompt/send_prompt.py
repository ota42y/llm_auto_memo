import os
import sys
import time
from pathlib import Path
from logging import getLogger

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from langchain_openai import ChatOpenAI


logger = getLogger(__name__)

class PromptSettings:
    def __init__(self, input_path: str):
        self.input_path = str(Path(input_path).resolve())
        self.need_refresh = False
    

class PromptHandler(FileSystemEventHandler):
    def __init__(self, prompt_settings: PromptSettings):
        super().__init__()
        self.prompt_settings = prompt_settings

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.src_path == self.prompt_settings.input_path:
            logger.info("update")
            self.prompt_settings.need_refresh = True

def send_llm_and_show(prompt_settings: PromptSettings):
    content = open(prompt_settings.input_path).read()
    logger.info(f"loaded {prompt_settings.input_path}")

    llm = ChatOpenAI(
        base_url="https://api.platform.preferredai.jp/v1",
        model="plamo-1.0-prime",
        streaming=True,
        # other params...,
    )

    messages=[
        {"role": "user", "content": content},
    ]
    print("\n")
    length = 0
    for chunk in llm.stream(messages):
        if prompt_settings.need_refresh:
            return # stop stream
        print(chunk.content, end="", flush=True)
        length += len(chunk.content)
    print("")
    logger.info(f"generated {length} characters")

        

def watch(prompt_settings: PromptSettings):
    event_handler = PromptHandler(prompt_settings=prompt_settings)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            if prompt_settings.need_refresh:
                prompt_settings.need_refresh = False
                send_llm_and_show(prompt_settings)
            
    finally:
        observer.stop()
        observer.join()


def send_prompt(prompt_settings: PromptSettings):
    send_llm_and_show(prompt_settings)


if __name__ == "__main__":
    # 引数から指定したファイルをロードする
    args = sys.argv
    if len(args) < 3:
        logger.error("usage: send_prompt.py command imput_path")
        sys.exit(1)

    input_path = args[2]
    if not os.path.isfile(input_path):
        logger.error(f"{input_path} is not a file")
        sys.exit(1)

    prompt_settings = PromptSettings(input_path=input_path)


    command = args[1]
    if command == "watch":
        watch(prompt_settings)
    elif command == "send":
        send_prompt(prompt_settings)
    else:
        logger.error(f"unknown command: {command}")
        sys.exit(1)
