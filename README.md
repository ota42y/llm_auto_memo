# 習慣化できない人向けの LLMライフログ

1. 画面をキャプチャ
2. キャプチャをOCR
3. OCRをLLMに説明させる
4. 30分ごとにやったことをレポートにまとめる
5. 指定フォルダ(`WORK_REPORT_ARCHIVE_DIR`)に保存
  - ファイル内にかかれている `report_added: YYYYMMDD-hhmmss` がどこまで保存したかのタグになっている
  - 最も新しいタグを残しておけば自由に編集可能


# 使い方

## セットアップ

LLMに送る用のプロンプトテンプレートを作成します、exampleをコピーしてください。
コピー先のファイルが利用されますが、自由に変更可能です。
```
cp ./templates/ocr_explanation.txt.example ./templates/ocr_explanation.txt 
cp ./templates/report_prompt.txt.example ./templates/report_prompt.txt
```


```bash
# before create folder
export WORK_REPORT_ARCHIVE_PATH=~/reports

export CAPTURE_FILE_NAME=com.YOUR_MAC_USERNAME.capturescreen.plist
export WORKINGNOTES_FILE_NAME=com.YOUR_MAC_USERNAME.workingnotes.plist

export CAPTURE_FILE_NAME=com.YOUR_MAC_USERNAME.capturescreen.plist

cp com.examples.capturescreen.plist $CAPTURE_FILE_NAME
cp com.examples.workingnotes.plist $WORKINGNOTES_FILE_NAME
# replace all com.ota42y.xxxxxx to com.YOUR_MAC_USERNAME.xxxxx in copied file

# replace all `WRITE_YOUR_PATH` to this folder
# replace WORK_REPORT_ARCHIVE_PATH to your archive path (see first line in this script)
# replace PATH to your path which support `uv` command

mv $CAPTURE_FILE_NAME ~/Library/LaunchAgents/$CAPTURE_FILE_NAME
launchctl load $CAPTURE_FILE_NAME

mv $WORKINGNOTES_FILE_NAME ~/Library/LaunchAgents/$WORKINGNOTES_FILE_NAME
launchctl load $WORKINGNOTES_FILE_NAME

# if you want stop run this command, if you want to reload stop before load
launchctl unload FILE_NAME
```

## 更新方法
pythonスクリプトに関しては実行ごとに読み込まれるので変更でreloadする必要はありません。
plistの
変更はreloadする必要があります。
