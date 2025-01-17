import sys
import datetime

from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

image_path = sys.argv[1]

models = [
    "mlx-community/Qwen2.5-VL-3B-Instruct-4bit",
    "mlx-community/Phi-3.5-vision-instruct-4bit",
    "mlx-community/deepseek-vl2-small-4bit",
    # "mlx-community/deepseek-vl2-4bit", # エラーで動かず
]

prompt = """
画面のスクリーンショットが与えられます。ここからどのような作業をしているかを予測し、
その中でも最も重要な内容を一つ選び、その内容について具体的に日本語で説明してください。
なお、絶対に理解した内容やアプリケーションの説明、内容に関わらないことについては言及しないでください。

回答は400文字以内を厳守してください。
"""

output_lines = [
    ["model", "duration", "output"]
]
for model_path in models:
    durations = []
    result_str = ""

    print("Loading model", model_path)
    model, processor = load(model_path, trust_remote_code=True)
    config = load_config(model_path)

    print("Applying chat template")
    formatted_prompt = apply_chat_template(
        processor, config, prompt, num_images=1
    )

    print("Generating output")
    for i in range(5):
        start = datetime.datetime.now()
        output = generate(model, processor, formatted_prompt, [image_path], verbose=False)
        duration = datetime.datetime.now() - start

        output_lines.append([model_path, duration.total_seconds(), output])
    open("out.csv", "w").write("\n".join([",".join(map(str, line)) for line in output_lines]))
