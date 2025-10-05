#!/bin/bash

# Link Extractor 起動スクリプト
# macOS/Linux用

set -e  # エラー時に停止

echo "🔗 Link Extractor 起動中..."
echo "================================"

# Python3の存在確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3がインストールされていません"
    echo "Homebrewでインストール: brew install python"
    exit 1
fi

# 仮想環境の作成（存在しない場合のみ）
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境をアクティベート
echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate

# pipのアップグレード
echo "⬆️  pipをアップグレード中..."
pip install --upgrade pip --quiet

# 依存関係のインストール
echo "📚 依存関係をインストール中..."
pip install -r requirements.txt --quiet

# データディレクトリの作成
mkdir -p link_extractor_data

echo "✅ セットアップ完了！"
echo "================================"
echo "🚀 Link Extractorを起動します..."
echo ""

# アプリケーション起動（ポート8080で起動）
echo "🌐 ブラウザで http://localhost:8080 にアクセスしてください"
python app.py