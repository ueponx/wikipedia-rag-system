"""
RAGシステムのインタラクティブテスト
"""

from rag_system import WikipediaRAG


def test_search():
    """類似情報検索のテスト"""
    rag = WikipediaRAG()
    
    query = input("\n検索キーワードを入力: ")
    n_results = int(input("取得件数 (デフォルト: 3): ") or "3")
    
    print(f"\n検索中: '{query}'...\n")
    results = rag.search_similar_content(query, n_results)
    
    if not results:
        print("関連する情報が見つかりませんでした。")
        return
    
    print(f"{len(results)}件の関連情報が見つかりました:\n")
    
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        print(f"--- [{i}] {metadata.get('title', '不明')} ---")
        print(f"類似度スコア: {1 - result['distance']:.4f}")
        print(f"ページID: {metadata.get('page_id', 'N/A')}")
        print(f"URL: {metadata.get('url', 'N/A')}")
        print(f"取得日時: {metadata.get('fetch_datetime', 'N/A')}")
        
        # 要約の表示（長い場合は切り詰め）
        summary = metadata.get('summary', '')
        if summary:
            display_summary = summary[:150] + '...' if len(summary) > 150 else summary
            print(f"要約: {display_summary}")
        
        # カテゴリの表示
        categories = metadata.get('categories', '')
        if categories:
            cat_list = categories.split(',')[:3]  # 最初の3件のみ
            print(f"カテゴリ: {', '.join(cat_list)}")
        
        print()


def test_qa():
    """質問応答のテスト"""
    rag = WikipediaRAG()
    
    query = input("\n質問を入力: ")
    
    print(f"\n回答を生成中...\n")
    answer = rag.generate_answer(query)
    
    print("=" * 60)
    print("【回答】")
    print("=" * 60)
    print(answer)
    print("=" * 60)


def interactive_mode():
    """インタラクティブモード"""
    rag = WikipediaRAG()
    
    print("\nインタラクティブモードを開始します")
    print("終了するには 'quit' または 'exit' と入力してください\n")
    
    while True:
        query = input("\n質問: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("終了します")
            break
        
        if not query:
            continue
        
        print("\n回答を生成中...\n")
        answer = rag.generate_answer(query)
        
        print("-" * 60)
        print(answer)
        print("-" * 60)


def show_statistics():
    """統計情報の表示"""
    rag = WikipediaRAG()
    stats = rag.get_collection_stats()
    
    print(f"\n統計情報:")
    print(f"  - コレクション名: {stats['collection_name']}")
    print(f"  - 登録記事数: {stats['total_documents']}件")
    
    # サンプルデータの表示
    if stats['total_documents'] > 0:
        print("\nサンプルデータ:")
        results = rag.collection.peek(limit=3)
        if results and results.get('metadatas'):
            for i, metadata in enumerate(results['metadatas'], 1):
                print(f"  {i}. {metadata.get('title', '不明')}")
                print(f"     ページID: {metadata.get('page_id', 'N/A')}")
                print(f"     カテゴリ数: {len(metadata.get('categories', '').split(','))}")


def main():
    """メインメニュー"""
    while True:
        print("\n" + "=" * 60)
        print("Wikipedia RAG システム - テストメニュー")
        print("=" * 60)
        print("1. 類似情報検索テスト")
        print("2. 質問応答テスト")
        print("3. インタラクティブモード")
        print("4. 統計情報の表示")
        print("5. 終了")
        print("=" * 60)
        
        choice = input("\n選択 (1-5): ").strip()
        
        if choice == '1':
            test_search()
        elif choice == '2':
            test_qa()
        elif choice == '3':
            interactive_mode()
        elif choice == '4':
            show_statistics()
        elif choice == '5':
            print("\n終了します")
            break
        else:
            print("\n無効な選択です")


if __name__ == "__main__":
    main()
