import sys
import datetime

image_path = sys.argv[1]

# [ ("ocr_name", "time", "result"), ("ocr_name", "time", "result") ]
outputs: list[tuple[str, str, str]] = []

def do_easyocr(image_path: str) -> tuple[str, str, str]:
    import easyocr
    reader = easyocr.Reader(['ja','en'])

    now = datetime.datetime.now()
    result = reader.readtext(image_path, detail = 0)
    duration = datetime.datetime.now() - now
    return ("do_easyocr", str(duration), "\n".join(result))


def do_yomitoku(image_path: str) -> tuple[str, str, str]:
    import yomitoku
    from yomitoku.data.functions import load_image

    analyzer = yomitoku.OCR(
        configs={},
        visualize=False,
        device='mps'
    )

    img = load_image(image_path)

    now = datetime.datetime.now()
    results, _ = analyzer(img)
    duration = datetime.datetime.now() - now

    texts = [w.content for w in results.words]
    return ("yomitoku", str(duration), "\n".join(texts))

for f in [do_easyocr, do_yomitoku]:
    try:
        outputs.append(f(image_path))
    except Exception as e:
        outputs.append((f.__name__, "error", str(e)))

import csv
with open('output.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows([["name"] + [r[0] for r in outputs]])
    writer.writerows([["time"] + [r[1] for r in outputs]])
    writer.writerows([["result"] + [r[2] for r in outputs]])
