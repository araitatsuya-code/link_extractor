#!/usr/bin/env python3
"""
Link Extractor Backend Server
Webサイトからリンクを抽出するためのFlaskサーバー
CORS制限を回避し、フロントエンドにAPIを提供
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)  # すべてのドメインからのCORSリクエストを許可

# データ保存用ディレクトリ
DATA_DIR = "link_extractor_data"
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

def ensure_data_dir():
    """データディレクトリの存在を確認"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_history():
    """履歴データを読み込み"""
    ensure_data_dir()
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"履歴読み込みエラー: {e}")
    return []

def save_history(data):
    """履歴データを保存"""
    ensure_data_dir()
    try:
        history = load_history()
        history.insert(0, data)
        
        # 最新50件のみ保持
        if len(history) > 50:
            history = history[:50]
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"履歴保存エラー: {e}")
        return False

def normalize_url(url, base_url, remove_query=True, remove_anchors=True):
    """URLを正規化"""
    try:
        full_url = urljoin(base_url, url)
        parsed = urlparse(full_url)
        
        # クエリパラメータとアンカーを除去
        if remove_query:
            parsed = parsed._replace(query='')
        if remove_anchors:
            parsed = parsed._replace(fragment='')
        
        return parsed.geturl()
    except Exception:
        return None

def extract_links_from_html(html, base_url, options=None):
    """HTMLからリンクを抽出"""
    if options is None:
        options = {
            'internal_only': True,
            'remove_query': True,
            'remove_anchors': True
        }
    
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    # すべてのaタグからhrefを抽出
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href or href == '#':
            continue
        
        # URLを正規化
        normalized_url = normalize_url(
            href, base_url, 
            options.get('remove_query', True),
            options.get('remove_anchors', True)
        )
        
        if normalized_url:
            links.append(normalized_url)
    
    # 重複除去
    unique_links = list(set(links))
    
    # 内部リンクのみフィルター
    if options.get('internal_only', True):
        base_domain = urlparse(base_url).netloc
        filtered_links = []
        for link in unique_links:
            try:
                if urlparse(link).netloc == base_domain:
                    filtered_links.append(link)
            except Exception:
                continue
        unique_links = filtered_links
    
    return sorted(unique_links)

def get_previous_data(url):
    """指定URLの前回データを取得"""
    history = load_history()
    for item in history:
        if item.get('base_url') == url:
            return item
    return None

@app.route('/')
def index():
    """フロントエンドのHTMLファイルを提供"""
    return send_from_directory('.', 'link_extractor.html')

@app.route('/api/extract', methods=['POST'])
def extract_links():
    """リンク抽出API"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URLが指定されていません'}), 400
        
        target_url = data['url'].strip()
        options = data.get('options', {})
        
        # URLの妥当性チェック
        try:
            parsed_url = urlparse(target_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return jsonify({'error': '有効なURLを指定してください'}), 400
        except Exception:
            return jsonify({'error': '無効なURL形式です'}), 400
        
        # Webページを取得
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(target_url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return jsonify({'error': f'Webページの取得に失敗しました: {str(e)}'}), 400
        
        # リンクを抽出
        all_links = extract_links_from_html(response.text, target_url, options)
        
        # 前回データとの差分を計算
        previous_data = get_previous_data(target_url)
        if previous_data:
            previous_links = set(previous_data.get('all_links', []))
            new_links = [link for link in all_links if link not in previous_links]
        else:
            new_links = all_links.copy()
        
        # 結果データ
        result = {
            'base_url': target_url,
            'all_links': all_links,
            'new_links': new_links,
            'timestamp': datetime.now().isoformat(),
            'total_count': len(all_links),
            'new_count': len(new_links),
            'options': options
        }
        
        # 履歴に保存
        save_history(result)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"抽出エラー: {e}")
        return jsonify({'error': f'予期しないエラーが発生しました: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """履歴取得API"""
    try:
        history = load_history()
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': f'履歴の取得に失敗しました: {str(e)}'}), 500

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """履歴クリアAPI"""
    try:
        ensure_data_dir()
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return jsonify({'success': True, 'message': '履歴をクリアしました'})
    except Exception as e:
        return jsonify({'error': f'履歴のクリアに失敗しました: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェックAPI"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    import sys
    
    # ポート番号を環境変数またはコマンドライン引数から取得
    port = int(os.environ.get('PORT', 5000))
    
    # コマンドライン引数でポート指定をチェック
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("無効なポート番号です。デフォルトの5000を使用します。")
    
    print("Link Extractor Backend Server")
    print("=" * 40)
    print(f"フロントエンド: http://localhost:{port}")
    print("API エンドポイント:")
    print("  POST /api/extract - リンク抽出")
    print("  GET  /api/history - 履歴取得")
    print("  DELETE /api/history - 履歴クリア")
    print("  GET  /api/health - ヘルスチェック")
    print("=" * 40)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ ポート {port} は既に使用されています。")
            print("\n解決方法:")
            print("1. 別のポートで起動: python app.py 8000")
            print("2. 環境変数で指定: PORT=8000 python app.py")
            print("3. macOSの場合: システム設定 > 一般 > AirDrop & Handoff > AirPlay Receiver をオフ")
            print("4. 使用中プロセス確認: lsof -i :5000")
        else:
            print(f"サーバー起動エラー: {e}")
        sys.exit(1)
