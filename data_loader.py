"""
Wikipediaデータローダー
markdownファイルから記事情報を抽出してChromaDBに登録
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, Any
from rag_system import WikipediaRAG
from tqdm import tqdm


def parse_wikipedia_markdown(file_path: str) -> Dict[str, Any]:
    """
    Wikipediaのmarkdownファイルをパース（実データ形式対応）
    
    Args:
        file_path: markdownファイルのパス
    
    Returns:
        記事情報の辞書
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # タイトルの抽出
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else os.path.basename(file_path)
    
    # ページIDの抽出
    page_id_match = re.search(r'\*\*ページID\*\*:\s*(\d+)', content)
    page_id = page_id_match.group(1) if page_id_match else ""
    
    # URLの抽出
    url_match = re.search(r'\*\*URL\*\*:\s*(.+)$', content, re.MULTILINE)
    url = url_match.group(1).strip() if url_match else ""
    
    # 言語の抽出
    lang_match = re.search(r'\*\*言語\*\*:\s*(\w+)', content)
    language = lang_match.group(1) if lang_match else ""
    
    # 取得日時の抽出
    datetime_match = re.search(r'\*\*取得日時\*\*:\s*(.+)$', content, re.MULTILINE)
    fetch_datetime = datetime_match.group(1).strip() if datetime_match else ""
    
    # 要約の抽出（---で区切られたセクションから）
    summary_match = re.search(
        r'---\s*##\s+要約\s*\n\s*(.+?)\s*---',
        content,
        re.DOTALL
    )
    summary = summary_match.group(1).strip() if summary_match else ""
    
    # カテゴリの抽出
    categories = []
    category_match = re.search(
        r'---\s*##\s+カテゴリ\s*\n(.+?)\s*---',
        content,
        re.DOTALL
    )
    if category_match:
        category_text = category_match.group(1)
        categories = [
            line.strip('- ').strip().replace('Category:', '')
            for line in category_text.split('\n')
            if line.strip().startswith('-')
        ]
    
    # セクション構造の抽出
    section_structure = []
    section_match = re.search(
        r'---\s*##\s+セクション構造\s*\n(.+?)\s*---',
        content,
        re.DOTALL
    )
    if section_match:
        section_text = section_match.group(1)
        for line in section_text.split('\n'):
            if line.strip().startswith('-'):
                section_structure.append(line.strip('- ').strip())
    
    # 本文の抽出
    body_match = re.search(
        r'---\s*##\s+本文\s*\n(.+?)(?:\n---\n|\Z)',
        content,
        re.DOTALL
    )
    body = body_match.group(1).strip() if body_match else ""
    
    # リンク情報の抽出（オプショナル）
    link_count_match = re.search(r'\*\*内部リンク総数\*\*:\s*(\d+)', content)
    link_count = link_count_match.group(1) if link_count_match else "0"
    
    return {
        'title': title,
        'page_id': page_id,
        'url': url,
        'language': language,
        'fetch_datetime': fetch_datetime,
        'summary': summary,
        'categories': categories,
        'section_structure': section_structure,
        'body': body,
        'link_count': link_count,
        'full_content': content
    }


def load_wikipedia_data(data_dir: str, reset: bool = False) -> None:
    """
    Wikipediaデータの読み込みと登録
    
    Args:
        data_dir: Wikipediaのmarkdownファイルが格納されているディレクトリ
        reset: Trueの場合、既存データをリセット
    """
    rag = WikipediaRAG()
    
    # リセット確認
    if reset:
        confirm = input("既存のデータをリセットしますか？ (y/N): ")
        if confirm.lower() == 'y':
            rag.client.delete_collection("wikipedia_articles")
            rag.collection = rag.client.get_or_create_collection(
                name="wikipedia_articles"
            )
            print("データをリセットしました。")
    
    # データディレクトリの存在確認
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"エラー: ディレクトリ '{data_dir}' が見つかりません。")
        return
    
    # markdownファイルの読み込み
    md_files = list(data_path.glob("*.md"))
    
    if not md_files:
        print(f"{data_dir} にmarkdownファイルが見つかりません。")
        return
    
    print(f"{len(md_files)}件のファイルを読み込みます...\n")
    
    # 各ファイルの処理
    success_count = 0
    error_count = 0
    
    for file_path in tqdm(md_files, desc="データ読み込み中"):
        try:
            # パース
            data = parse_wikipedia_markdown(str(file_path))
            
            # ChromaDBに登録
            doc_id = f"wiki_{data['page_id']}" if data['page_id'] else f"wiki_{file_path.stem}"
            
            rag.collection.add(
                documents=[data['full_content']],
                metadatas=[{
                    'title': data['title'],
                    'page_id': data['page_id'],
                    'url': data['url'],
                    'language': data['language'],
                    'fetch_datetime': data['fetch_datetime'],
                    'summary': data['summary'][:500],  # 500文字に制限
                    'categories': ','.join(data['categories'][:10]),  # 上位10件
                    'link_count': data['link_count'],
                    'source': str(file_path)
                }],
                ids=[doc_id]
            )
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"\nエラー ({file_path.name}): {e}")
    
    # 統計情報の表示
    stats = rag.get_collection_stats()
    print(f"\n完了: {success_count}件の記事を登録しました")
    if error_count > 0:
        print(f"エラー: {error_count}件の記事で問題が発生しました")
    print(f"データベース総数: {stats['total_documents']}件")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Wikipedia記事をChromaDBに読み込みます'
    )
    parser.add_argument(
        '--data-dir',
        default='./data/wikipedia',
        help='Wikipediaのmarkdownファイルが格納されているディレクトリ (デフォルト: ./data/wikipedia)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='既存のデータをリセットしてから読み込む'
    )
    
    args = parser.parse_args()
    
    print("=== Wikipedia RAG データローダー ===\n")
    print(f"データディレクトリ: {args.data_dir}\n")
    
    # データの読み込み
    load_wikipedia_data(args.data_dir, args.reset)


if __name__ == "__main__":
    main()
