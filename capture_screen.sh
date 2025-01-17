#!/bin/bash

for i in {1..10} ; do
    # windowが規定個数以下だった場合はエラーになって終わるが、とっても意味がないものなのでskip
    export RECT=$(osascript -e "tell application \"System Events\" to tell (first process whose frontmost is true) to return {position, size} of window $i")
    export WINDOW_NAME=$(osascript -e "tell application \"System Events\" to tell (first process whose frontmost is true) to return {name, name of window $i}")

    # screencaptureはスペースを含むとエラーになるので削除
    export RECT=`echo $RECT | tr -d ' '`
    w=$(cut -d ',' -f 3 <<< $RECT)
    h=$(cut -d ',' -f 4 <<< $RECT)

    # 画像サイズが720pxより小さかったら他のを取る
    # retinaなので半分の360
    if [ $w -lt 360 ]; then
        continue
    fi
    if [ $h -lt 360 ]; then
        continue
    fi
    break
done


output_root="./images"
output_dir="${output_root}/$(date +%Y%m%d)"
output_file_base="${output_dir}/$(date +%Y%m%d-%H%M%S)"

mkdir -p $output_dir

# -R で範囲を指定
# -x 音を付けない
screencapture -R $RECT -x "${output_file_base}.png"
echo $WINDOW_NAME > "${output_file_base}.txt"
