@echo off
chcp 65001 >nul
echo ============================================================
echo  微軟文件轉 Markdown 工具  by 阿剛老師
echo ============================================================
echo.

:: 安裝相依套件（若已安裝則略過）
echo [1/2] 檢查並安裝相依套件...
pip install -r requirements.txt --quiet

echo.
echo [2/2] 啟動程式...
python app.py

if errorlevel 1 (
    echo.
    echo 程式發生錯誤，請確認已安裝 Python 3.10 以上版本。
    pause
)
