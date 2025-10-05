@echo off
REM Link Extractor 起動スクリプト
REM Windows用

echo 🔗 Link Extractor 起動中...
echo ================================

REM Pythonの存在確認
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Pythonがインストールされていません
    echo https://www.python.org/downloads/ からダウンロードしてください
    pause
    exit /b 1
)

REM 仮想環境の作成（存在しない場合のみ）
if not exist "venv" (
    echo 📦 仮想環境を作成中...
    python -m venv venv
)

REM 仮想環境をアクティベート
echo 🔧 仮想環境をアクティベート中...
call venv\Scripts\activate.bat

REM pipのアップグレード
echo ⬆️  pipをアップグレード中...
pip install --upgrade pip --quiet

REM 依存関係のインストール
echo 📚 依存関係をインストール中...
pip install -r requirements.txt --quiet

REM データディレクトリの作成
if not exist "link_extractor_data" mkdir link_extractor_data

echo ✅ セットアップ完了！
echo ================================
echo 🚀 Link Extractorを起動します...
echo.

REM アプリケーション起動（ポート8080で起動）
echo 🌐 ブラウザで http://localhost:8080 にアクセスしてください
python app.py

pause