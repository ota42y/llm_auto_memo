import sys
import datetime

image_path = sys.argv[1]

from typing import List, Tuple

class TextBox:
    """
    テキストと、そのテキストが描画されている矩形領域を保持するクラス
    x, yは左上座標、w, hは幅と高さ
    """
    def __init__(self, text: str, x: int, y: int, w: int, h: int):
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __repr__(self):
        return f"TextBox(text={self.text}, x={self.x}, y={self.y}, w={self.w}, h={self.h})"


def can_merge(rect1: TextBox, rect2: TextBox, d: int, me: int) -> bool:
    """
    2つの矩形 rect1, rect2 が「結合条件」を満たすか判定する。
    矩形は (x, y, w, h) の形式。
    距離 d 以下、かつ「x 軸・y 軸がほぼ同じライン上で右隣／下隣」にあるかどうか。
    """

    # OCRの関係上、若干左に寄るが実際は同じものがあり得るので、b分だけ許容範囲を増やす
    x1, y1, w1, h1 = rect1.x - me, rect1.y - me, rect1.w + me, rect1.h + me
    x2, y2, w2, h2 = rect2.x, rect2.y, rect2.w, rect2.h
    
    # rect1, rect2 の左上・右下座標
    left1,  right1  = x1, x1 + w1
    top1,   bottom1 = y1, y1 + h1
    left2,  right2  = x2, x2 + w2
    top2,   bottom2 = y2, y2 + h2

    # --- 1) rect2 の左上 (x2,y2) が rect1 内に入っているかどうか ---
    overlap_condition = (left1 <= left2 <= right1) and (top1 <= top2 <= bottom1)

    # --- 2) 水平方向・垂直方向で隣接しているかどうか ---
    # 垂直方向がほぼ同じかどうか (top 同士が d 以内)
    same_horizontal_line = abs(top1 - top2) <= d
    # 水平方向がほぼ同じかどうか (left 同士が d 以内)
    same_vertical_line   = abs(left1 - left2) <= d

    # 水平方向に隣接
    horizontally_adjacent = False
    if same_horizontal_line:
        # rect2 が rect1 の右側
        if left2 >= right1 and (left2 - right1) <= d:
            horizontally_adjacent = True
        # rect1 が rect2 の右側
        if left1 >= right2 and (left1 - right2) <= d:
            horizontally_adjacent = True

    # 垂直方向に隣接
    vertically_adjacent = False
    if same_vertical_line:
        # rect2 が rect1 の下側
        if top2 >= bottom1 and (top2 - bottom1) <= d:
            vertically_adjacent = True
        # rect1 が rect2 の下側
        if top1 >= bottom2 and (top1 - bottom2) <= d:
            vertically_adjacent = True

    return overlap_condition or horizontally_adjacent or vertically_adjacent

def merge_boxes(box1: TextBox, box2: TextBox) -> TextBox:
    """
    2つのボックスを結合し、テキストを連結した新しいボックスを作成する。
    結合後のボックスの領域は、2つのボックスの外接矩形を取る。
    """
    # 新しい左上 x, y
    new_x = min(box1.x, box2.x)
    new_y = min(box1.y, box2.y)
    # 新しい右下 x, y
    new_x2 = max(box1.x + box1.w, box2.x + box2.w)
    new_y2 = max(box1.y + box1.h, box2.y + box2.h)
    # 新しい幅, 高さ
    new_w = new_x2 - new_x
    new_h = new_y2 - new_y
    # テキストは単純に連結 (必要に応じて改行を挟むなど調整)
    new_text = box1.text + box2.text

    return TextBox(new_text, new_x, new_y, new_w, new_h)


def get_soreted_boxes(boxes: List[TextBox]) -> List[TextBox]:
    return sorted(boxes, key=lambda b: (b.x, b.y))


def merge_nearby_boxes(boxes: List[TextBox], d: int, me: int) -> List[TextBox]:
    """
    与えられた boxes のうち、距離 d 以下のものを結合して新しいリストを返す。
    結合可能なペアが見つからなくなるまで繰り返す。
    """
    boxes = get_soreted_boxes(boxes)
    merged = True
    while merged:
        merged = False
        new_boxes = []
        used = set()

        for i in range(len(boxes)):
            if i in used:
                continue

            for j in range(i + 1, len(boxes)):
                if j in used:
                    continue
                if can_merge(boxes[i], boxes[j], d, me):
                    # 2つをマージして新しいボックスを作成
                    merged_box = merge_boxes(boxes[i], boxes[j])
                    new_boxes.append(merged_box)
                    used.add(i)
                    used.add(j)
                    merged = True
                    break  # i番目はjとマージしたので、次のiへ行く

            if i not in used:
                # マージされなかったボックスはそのまま残す
                new_boxes.append(boxes[i])

        boxes = get_soreted_boxes(new_boxes)

    return boxes

if __name__ == "__main__":
    # サンプル入力
    boxes = [
        #TextBox("Hello",  10,  10,  50, 20),
        #TextBox("World",  70,  15,  50, 20),
        #TextBox("Foo",    130, 12,  40, 20),
        #TextBox("Bar",    200, 10,  40, 20),
        #TextBox("Baz",    10,  40,  50, 20),
        TextBox("Hello",  10,  10,  10, 100),
        TextBox("World",  15,  15,  20, 20),
    ]

    # d 以下の場合に結合 (垂直 or 水平のどちらかが d 以下)
    d = 10
    # OCRによって領域判定が若干増えてしまったときの誤差許容度
    me = 5

    print("----- マージ前 -----")
    for b in boxes:
        print(b)

    merged_boxes = merge_nearby_boxes(boxes, d, me)

    from PIL import Image, ImageDraw
    im = Image.new('RGB', (300, 300), (128, 128, 128))
    draw = ImageDraw.Draw(im)   
    for b in boxes:
        draw.rectangle([b.x, b.y, b.x + b.w, b.y + b.h], outline=(255, 0, 0))
    im.save('tmp/out.png')

    
    for m in merged_boxes:
        print(m)

    im = Image.new('RGB', (300, 300), (128, 128, 128))
    draw = ImageDraw.Draw(im)   
    for b in merged_boxes:
        draw.rectangle([b.x, b.y, b.x + b.w, b.y + b.h], outline=(255, 0, 0))
    im.save('tmp/out2.png')


DISTANCE_THRESHOLD = 20
SIZE_THRESHOLD = 5
TEXT_LENGTH_THREASHOLD = 10

import easyocr


def ocr_file(img_path: str, reader: easyocr.Reader) -> list[TextBox]:
    results = reader.readtext(img_path)

    boxes: list[TextBox] = []
    for r in results:
        # [[np.int32(1), np.int32(1)], [np.int32(2), np.int32(1)], [np.int32(2), np.int32(1)], [np.int32(2), np.int32(2)]]
        x_points = []
        y_points = []
        for p in r[0]:
            x_points.append(int(p[0]))
            y_points.append(int(p[1]))
        x_points.sort()
        y_points.sort()
        boxes.append(TextBox(
            r[1],
            x_points[0],
            y_points[0],
            x_points[-1] - x_points[0],
            y_points[-1] - y_points[0],
        ))

    merges = merge_nearby_boxes(boxes, DISTANCE_THRESHOLD, SIZE_THRESHOLD)
    return [box for box in merges if len(box.text) > TEXT_LENGTH_THREASHOLD]

import easyocr
reader = easyocr.Reader(['ja','en'])

result = reader.readtext(image_path)

print(type(result[0]))
print(ocr_file(image_path, reader))
