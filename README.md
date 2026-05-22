# 微軟文件轉 Markdown 工具

> 基於 [Microsoft MarkItDown](https://github.com/microsoft/markitdown) 的現代化圖形介面，
> 讓任何人都能輕鬆將各種文件格式批次轉換為 Markdown。

**Made by [阿剛老師](https://kentxchang.blogspot.tw)**　｜　本專案以 **CC BY-NC-SA 4.0** 授權釋出

---

## 目錄

- [功能特色](#功能特色)
- [支援格式](#支援格式)
- [安裝 Python](#安裝-python)
- [安裝套件](#安裝套件)
- [啟動程式](#啟動程式)
- [使用說明](#使用說明)
  - [單檔轉換](#單檔轉換)
  - [批次轉換](#批次轉換)
  - [音訊轉文字](#音訊轉文字)
- [原始程式來源](#原始程式來源)
- [授權聲明](#授權聲明)

---

## 功能特色

| 功能 | 說明 |
|------|------|
| 📄 單檔轉換 | 選取或貼上路徑／URL，一鍵轉為 Markdown，可即時預覽、複製或存檔 |
| 📦 批次轉換 | 一次加入多個檔案或整個資料夾，統一輸出到指定目錄 |
| 🌐 URL 支援 | 批次清單可直接加入網址（含 YouTube），自動命名輸出檔 |
| 🎙️ 音訊轉文字 | 支援本機 Whisper（免費、離線）或 OpenAI Whisper API |
| 🌙 深色／淺色 | 自動跟隨系統外觀設定 |
| 🖥️ 一鍵安裝 | 缺少套件時彈出安裝輔助視窗，可直接在 GUI 中觸發 pip install |

---

## 支援格式

| 類別 | 副檔名 |
|------|--------|
| 文件 | `.pdf` `.docx` `.doc` `.pptx` `.ppt` `.xlsx` `.xls` |
| 網頁 | `.html` `.htm` |
| 資料 | `.csv` `.json` `.xml` |
| 電子書 | `.epub` |
| 圖片 | `.jpg` `.jpeg` `.png` `.gif` `.bmp` `.webp` |
| 音訊／影片 | `.mp3` `.mp4` `.wav` `.m4a` `.flac` `.ogg` `.aac` |
| 壓縮檔 | `.zip` |
| 郵件 | `.msg`（Outlook） |
| 網址 | YouTube URL、一般網頁 URL |

---

## 安裝 Python

本程式需要 **Python 3.10 以上版本**。

### Windows

1. 前往 [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. 下載最新的 **Windows installer（64-bit）**
3. 執行安裝程式，**務必勾選「Add Python to PATH」**
4. 安裝完成後，開啟「命令提示字元」或「PowerShell」，輸入以下指令確認版本：

```
python --version
```

應顯示類似 `Python 3.12.x` 的版本號碼。

### macOS

建議使用 Homebrew 安裝：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python
```

或至官網下載 macOS 安裝包：[https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/)

### Linux（Ubuntu / Debian）

```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

> ⚠️ Linux 需確認 `tkinter` 已安裝（`python3-tk`），否則 GUI 無法啟動。

---

## 安裝套件

### 方法一：使用 run.bat（Windows，最簡單）

直接雙擊專案目錄中的 **`run.bat`**，它會自動安裝所有必要套件並啟動程式。

### 方法二：手動安裝

開啟終端機，切換到專案目錄後執行：

```bash
pip install -r requirements.txt
```

`requirements.txt` 包含：

```
customtkinter>=5.2.0
markitdown[all]>=0.1.0
```

### 音訊轉文字（擇一安裝）

若需要轉換音訊檔（MP3、WAV、MP4 等），請依需求擇一安裝：

#### 方案 A：本機 Whisper（免費、不需 API Key、可離線）

```bash
pip install openai-whisper
```

本機 Whisper **另需安裝 ffmpeg**：

| 系統 | 安裝指令 |
|------|---------|
| Windows（winget） | `winget install ffmpeg` |
| Windows（Chocolatey） | `choco install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Linux | `sudo apt install ffmpeg` |
| 手動下載 | [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) |

> 首次使用時會自動從網路下載 Whisper 模型（75 MB ～ 3 GB，依選擇的模型大小而定）。
> 下載完成後即可完全離線使用。

#### 方案 B：OpenAI Whisper API（雲端，需 API Key）

```bash
pip install openai
```

需在程式內的「⚙ 轉錄設定」填入 OpenAI API Key（格式：`sk-…`）。
API Key 可至 [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) 申請。

---

## 啟動程式

### Windows

雙擊 `run.bat`，或在命令提示字元中執行：

```bat
python app.py
```

### macOS / Linux

```bash
python3 app.py
```

---

## 使用說明

### 單檔轉換

1. 點選「**單檔轉換**」分頁
2. 在「來源」欄位：
   - 點「**瀏覽**」選取本機檔案，或
   - 直接貼上 **YouTube URL** 或其他網址
3. 點「**▶ 轉換**」
4. 轉換完成後可：
   - 「**複製**」— 將 Markdown 複製到剪貼簿
   - 「**儲存 .md**」— 另存為 Markdown 檔案
   - 「**清除**」— 清空輸出區

### 批次轉換

1. 點選「**批次轉換**」分頁
2. 設定「**輸出資料夾**」（留空則輸出到各原始檔所在目錄；清單含有 URL 時必須指定）
3. 新增來源：
   - 「**新增檔案**」— 一次選取多個檔案
   - 「**新增資料夾**」— 掃描資料夾內所有支援格式（含子目錄）
   - 「**新增網址**」— 在輸入框貼上 URL 後按 Enter 或「新增網址」
4. 在清單中可多選後「**移除選取**」，或「**清除全部**」重置
5. 點「**▶ 開始批次轉換**」
   - 進度條即時顯示整體進度
   - 清單每列顯示該檔狀態：等待中 → 轉換中 → 完成／失敗
6. 完成後彈出統計視窗（幾個成功、幾個失敗）

> **輸出命名規則：** 輸出檔名與原始檔名相同（副檔名改為 `.md`）；若目標路徑已存在相同檔名，自動加上 `_1`、`_2` 後綴避免覆蓋。

### 音訊轉文字

1. 點右上角「**⚙ 轉錄設定**」
2. 選擇轉錄方式：
   - **本機 Whisper（免費）**：選擇模型大小（推薦 `base`，約 145 MB）
   - **OpenAI API（需 Key）**：填入 API Key
3. 儲存設定
4. 回主畫面正常選取音訊檔案轉換

> 若尚未安裝 `openai-whisper`，程式會自動彈出「**安裝輔助視窗**」，
> 可在視窗內點「立即安裝」自動完成安裝，也可複製指令到終端機手動安裝。

**本機模型大小選擇參考：**

| 模型 | 大小 | 說明 |
|------|------|------|
| tiny | ~75 MB | 速度最快，適合短音訊或快速測試 |
| base | ~145 MB | **推薦**，速度與精準度平衡 |
| small | ~480 MB | 精準度佳 |
| medium | ~1.5 GB | 高精準度 |
| large | ~3 GB | 最高精準度，需較多記憶體 |

---

## 原始程式來源

本工具的核心轉換引擎來自 **Microsoft MarkItDown**：

- **GitHub**：[https://github.com/microsoft/markitdown](https://github.com/microsoft/markitdown)
- **作者**：Microsoft Corporation
- **授權**：MIT License

MarkItDown 是一套開源的 Python 函式庫，能夠將多種文件格式轉換為 Markdown，
廣泛應用於 AI 應用的文件前處理。

本專案在 MarkItDown 之上開發了圖形化使用介面（GUI），使用以下技術：

| 套件 | 用途 | 來源 |
|------|------|------|
| [MarkItDown](https://github.com/microsoft/markitdown) | 核心文件轉換引擎 | Microsoft |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | 現代化 GUI 框架 | Tom Schimansky |
| [openai-whisper](https://github.com/openai/whisper) | 本機語音辨識模型 | OpenAI |
| [openai-python](https://github.com/openai/openai-python) | OpenAI API 用戶端 | OpenAI |

---

## 授權聲明

本程式的**圖形介面部分**由 **[阿剛老師](https://kentxchang.blogspot.tw)** 開發，
以 **[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hant)** 授權釋出。

**您可以：**
- ✅ **分享** — 以任何媒介或格式重製及散布本素材
- ✅ **改作** — 重混、轉換本素材，及依本素材建立新素材

**但須遵守以下條件：**
- 📌 **姓名標示** — 須適當標示作者（阿剛老師）並附上授權連結
- 🚫 **非商業性** — 不得將本素材用於商業目的
- 🔄 **相同方式分享** — 若改作本素材，須以相同授權條款發布

核心轉換引擎 MarkItDown 版權歸 Microsoft Corporation 所有，依 MIT License 授權使用。
