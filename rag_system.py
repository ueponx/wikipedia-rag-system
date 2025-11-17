"""
Wikipedia RAGシステム - メイン実装
ChromaDBとGemini APIを使用した一般的な情報検索・質問応答システム
"""

import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from dotenv import load_dotenv


class WikipediaRAG:
    """Wikipedia情報を活用したRAGシステム"""
    
    def __init__(
        self,
        chroma_db_path: str = "./chroma_db",
        collection_name: str = "wikipedia_articles"
    ):
        """
        RAGシステムの初期化
        
        Args:
            chroma_db_path: ChromaDBの永続化パス
            collection_name: コレクション名
        """
        # 環境変数の読み込み
        load_dotenv()
        
        # Gemini APIの設定
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        
        # 環境変数からモデル名を取得（デフォルトはgemini-2.5-flash）
        model_name = os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash')
        self.model = genai.GenerativeModel(model_name)
        print(f"使用モデル: {model_name}")
        
        # ChromaDBの初期化（永続化）
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # コレクションの取得または作成
        try:
            self.collection = self.chroma_client.get_collection(
                name=collection_name
            )
            print(f"既存のコレクション '{collection_name}' を読み込みました")
        except:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Wikipedia記事情報コレクション"}
            )
            print(f"新しいコレクション '{collection_name}' を作成しました")
    
    def search_similar_content(
        self,
        query: str,
        n_results: int = 3,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        類似記事を検索
        
        Args:
            query: 検索クエリ
            n_results: 取得する結果数
            where: メタデータフィルタ
        
        Returns:
            検索結果のリスト
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        # 結果を整形
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results
    
    def generate_answer(
        self,
        query: str,
        n_results: int = 3,
        temperature: float = 0.7
    ) -> str:
        """
        RAGを使用して質問に回答
        
        Args:
            query: 質問内容
            n_results: 参考にする記事数
            temperature: 生成の創造性（0.0-1.0）
        
        Returns:
            生成された回答
        """
        # 類似記事を検索
        similar_articles = self.search_similar_content(query, n_results)
        
        # コンテキストの構築
        context = self._build_context(similar_articles)
        
        # プロンプトの構築
        prompt = self._build_prompt(query, context)
        
        # Gemini APIで生成
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=8000,
        )
        
        # Safety設定
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # レスポンスの詳細確認
            if not response.candidates:
                return "⚠️ レスポンスが生成されませんでした（候補が空）"
            
            candidate = response.candidates[0]
            
            # finish_reasonを確認
            finish_reason = candidate.finish_reason
            if finish_reason != 1:  # 1 = STOP (正常終了)
                reason_map = {
                    2: "MAX_TOKENS（トークン数上限）",
                    3: "SAFETY（セーフティフィルタ）",
                    4: "RECITATION（引用検出）",
                    5: "OTHER（その他）"
                }
                reason_text = reason_map.get(finish_reason, f"不明({finish_reason})")
                print(f"⚠️ 警告: 生成が途中で終了しました - 理由: {reason_text}")
            
            # テキストを取得
            parts = candidate.content.parts
            text_parts = [part.text for part in parts if hasattr(part, 'text')]
            result = ''.join(text_parts)
            
            if not result.strip():
                return "⚠️ 空のレスポンスが返されました"
            
            return result
                
        except Exception as e:
            return f"❌ エラーが発生しました: {str(e)}"
    
    def _build_context(self, similar_articles: List[Dict[str, Any]]) -> str:
        """類似記事からコンテキストを構築"""
        context_parts = []
        
        for i, article in enumerate(similar_articles, 1):
            metadata = article['metadata']
            context_parts.append(
                f"【参考情報{i}】\n"
                f"タイトル: {metadata.get('title', 'N/A')}\n"
                f"カテゴリ: {metadata.get('categories', 'N/A')}\n"
                f"内容:\n{article['document'][:800]}...\n"
            )
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """プロンプトを構築"""
        prompt = f"""# 質問応答タスク

あなたは親切で知識豊富なAIアシスタントです。以下の参考情報を元に、ユーザーの質問に正確かつ分かりやすく回答してください。

## ユーザーの質問
{query}

## 参考情報（Wikipedia記事から抽出）
{context}

## 回答の指針
1. 参考情報に基づいて正確に回答する
2. 分かりやすく、構造的に説明する
3. 必要に応じて具体例を挙げる
4. 参考情報に含まれていない内容を推測で補完しない
5. 専門用語は適切に説明する

それでは、質問に対する回答をお願いします。
"""
        return prompt
    
    def get_collection_stats(self):
        """コレクションの統計情報を取得"""
        count = self.collection.count()
        return {
            "total_documents": count,
            "collection_name": self.collection.name
        }


def main():
    """デモ実行"""
    print("=== Wikipedia RAGシステム ===\n")
    
    # RAGシステムの初期化
    rag = WikipediaRAG()
    
    # 統計情報の表示
    stats = rag.get_collection_stats()
    print(f"登録記事数: {stats['total_documents']}")
    
    if stats['total_documents'] == 0:
        print("\n⚠️  記事データが登録されていません")
        print("まず data_loader.py を実行してデータを登録してください\n")
        return
    
    # テスト検索
    print("\n--- 類似情報検索テスト ---")
    query = "機械学習"
    print(f"検索クエリ: {query}")
    results = rag.search_similar_content(query, n_results=2)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['metadata']['title']}")
        print(f"   ページID: {result['metadata'].get('page_id', 'N/A')}")
        print(f"   カテゴリ: {result['metadata'].get('categories', 'N/A')}")
    
    # 質問応答テスト
    print("\n\n--- 質問応答テスト ---")
    question = "機械学習とディープラーニングの違いは何ですか？"
    print(f"質問: {question}\n")
    
    print("生成中...\n")
    answer = rag.generate_answer(question, n_results=3)
    print(answer)


if __name__ == "__main__":
    main()
