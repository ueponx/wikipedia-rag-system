# Wikipedia RAGシステム

ChromaDBとGoogle Gemini APIを使用した、Wikipedia情報を活用するRAG（Retrieval-Augmented Generation）システムです。

## 概要

このシステムは以下の機能を提供します：

1. **情報検索**: Wikipediaデータから関連情報を検索
2. **質問応答**: 検索した情報を元にGemini APIが質問に回答

## システム構成

```
wikipedia-rag/
├── README.md              # このファイル
├── pyproject.toml         # uvプロジェクト設定
├── requirements.txt       # 依存パッケージリスト
├── .env                   # API設定ファイル（自分で作成）
├── rag_system.py          # RAGシステム本体
├── data_loader.py         # データ読み込みスクリプト
├── test_rag.py            # テスト・デモスクリプト
├── data/
│   └── wikipedia/         # Wikipediaのmarkdownファイルを配置
└── chroma_db/             # ChromaDBの永続化データ（自動生成）
```

## 必要な環境

- Python 3.8以上
- uv（Pythonパッケージマネージャー）
- Google Gemini API キー（無料枠あり）

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/wikipedia-rag.git
cd wikipedia-rag
```

### 2. uvのインストール（未インストールの場合）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. プロジェクトの初期化と依存パッケージのインストール

```bash
# 仮想環境の作成
uv venv

# 仮想環境の有効化
# macOS/Linuxの場合:
source .venv/bin/activate
# Windowsの場合:
.venv\Scripts\activate

# 依存パッケージのインストール
uv pip install -r requirements.txt
```

### 4. Google Gemini APIキーの取得

1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. 「Get API Key」をクリックしてAPIキーを生成
3. 生成されたAPIキーをコピー

### 5. 環境設定ファイルの作成

プロジェクトのルートディレクトリに `.env` ファイルを作成：

```bash
# .env ファイルの内容
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=models/gemini-2.5-pro
```

**注意**: `your_api_key_here` を実際のAPIキーに置き換えてください。

使用可能なモデル（2025年11月時点）：
- `models/gemini-2.5-pro` - 高性能モデル
- `models/gemini-2.5-flash` - 高速モデル（推奨）
- `models/gemini-1.5-pro` - 旧世代の高性能モデル
- `models/gemini-1.5-flash` - 旧世代の高速モデル

### 6. Wikipediaデータの準備

Wikipediaのmarkdownファイルを `data/wikipedia/` ディレクトリに配置します。

**markdownファイルの形式例**（WikipediaAPIで取得したデータ形式）:

```markdown
# 機械学習

**ページID**: 185375  
**URL**: https://ja.wikipedia.org/wiki/%E6%A9%9F%E6%A2%B0%E5%AD%A6%E7%BF%92  
**言語**: ja  
**取得日時**: 2025-11-10T22:43:32.686744  

---

## 要約

機械学習（きかいがくしゅう、英: machine learning）とは、経験からの学習により
自動で改善するコンピューターアルゴリズムもしくはその研究領域で、人工知能の
一種であるとみなされている。

---

## カテゴリ

- Category:機械学習
- Category:サイバネティックス
- Category:人工知能

---

## セクション構造

- **定義** (レベル 0)
- **理論** (レベル 0)
  - **統計的機械学習** (レベル 1)

---

## 本文

機械学習（きかいがくしゅう、英: machine learning）とは...
（詳細な本文が続く）
```

データの準備方法については、別途WikipediaAPIを使用したデータ取得スクリプトを参照してください。

### 7. データの読み込み

```bash
# 基本的な実行（data/wikipediaディレクトリのデータを使用）
python data_loader.py

# データディレクトリを指定して実行
python data_loader.py --data-dir ./my_data/wiki

# 既存データをリセットして読み込み
python data_loader.py --reset

# ヘルプの表示
python data_loader.py --help
```

実行すると：
- 指定したディレクトリ内の全markdownファイルが読み込まれます
- 各ファイルがパースされてメタデータが抽出されます
- ChromaDBに保存されます
- 登録件数が表示されます

### 8. システムのテスト

```bash
python test_rag.py
```

テストメニューから以下を試せます：
1. 類似情報検索テスト - キーワードで関連記事を検索
2. 質問応答テスト - 自然言語での質問に回答
3. インタラクティブモード - 対話的に連続で質問可能
4. 統計情報の表示 - 登録されている記事数を確認

## 使い方

### Pythonスクリプトから直接使用

```python
from rag_system import WikipediaRAG

# RAGシステムの初期化
rag = WikipediaRAG()

# 情報検索
results = rag.search_similar_content("機械学習", n_results=3)
for result in results:
    metadata = result['metadata']
    print(f"タイトル: {metadata['title']}")
    print(f"ページID: {metadata['page_id']}")
    print(f"カテゴリ: {metadata['categories']}")

# 質問応答
answer = rag.generate_answer("機械学習とディープラーニングの違いは何ですか？")
print(answer)
```

### 質問例

以下のような質問で試してみてください：

- 「機械学習の定義を教えてください」
- 「自然言語処理の応用例は？」
- 「機械学習と自然言語処理の関係について説明してください」
- 「ディープラーニングの特徴は何ですか？」

## カスタマイズ

### 検索結果数の調整

```python
# より多くの情報を参照して回答
answer = rag.generate_answer(
    query="質問内容",
    n_results=5  # デフォルトは3
)
```

### メタデータフィルタリング

実データのメタデータを活用して検索を絞り込めます：

```python
# 特定のカテゴリで検索
results = rag.collection.query(
    query_texts=["機械学習の応用"],
    n_results=3,
    where={"categories": {"$contains": "機械学習"}}
)

# 複数条件の組み合わせ
results = rag.collection.query(
    query_texts=["深層学習"],
    n_results=3,
    where={
        "$and": [
            {"categories": {"$contains": "機械学習"}},
            {"language": "ja"}
        ]
    }
)
```

### 生成パラメータの調整

```python
answer = rag.generate_answer(
    query="質問内容",
    temperature=0.9  # 0.0〜1.0、デフォルトは0.7
)
```

- **temperature=0.0**: より確定的で一貫性のある回答
- **temperature=1.0**: より創造的で多様な回答

### モデルの変更

`.env`ファイルでGeminiモデルを変更：

```bash
# より高性能なモデル
GEMINI_MODEL=models/gemini-2.5-pro

# より高速なモデル（推奨）
GEMINI_MODEL=models/gemini-2.5-flash
```

## トラブルシューティング

### エラー: GOOGLE_API_KEY not found

- `.env`ファイルが正しい場所（プロジェクトルート）に配置されているか確認
- APIキーが正しく設定されているか確認

### エラー: 記事データが登録されていません

- `data_loader.py`を実行してデータを読み込んでください
- `data/wikipedia/`にmarkdownファイルがあるか確認

### データベースの統計確認

```python
from rag_system import WikipediaRAG
rag = WikipediaRAG()
stats = rag.get_collection_stats()
print(stats)
```

## システム構成の詳細

### 各Pythonプログラムの役割

#### 1. rag_system.py（RAGシステムの中心）
- ChromaDBとの接続・管理
- ベクトル検索による類似情報の取得
- Gemini APIを使った回答生成
- 検索結果からのコンテキスト構築

#### 2. data_loader.py（データ登録ツール）
- Wikipediaのmarkdownファイルの読み込み
- ファイルのパースとメタデータ抽出
- ChromaDBへのデータ登録
- バッチ処理による効率的なデータ投入

#### 3. test_rag.py（テスト・デモツール）
- インタラクティブなメニューインターフェース
- 類似検索のテスト機能
- 質問応答のテスト機能
- 対話型の連続質問モード

## RAGシステムについて

RAGは以下の3ステップで動作します：

1. **検索（Retrieval）** - 質問に関連する情報をデータベースから検索
2. **拡張（Augmentation）** - 検索した情報をコンテキストとして整理
3. **生成（Generation）** - LLMが検索情報を参照しながら回答を生成

本来、LLMは学習データの範囲内でしか回答できませんが、RAGを使うことで最新情報や専門知識を活用した回答が可能になります。

## 技術スタック

- **Python 3.8+** - プログラミング言語
- **uv** - 高速なPythonパッケージマネージャー
- **ChromaDB** - ベクトルデータベース（埋め込みベクトルの自動生成、類似度検索）
- **Google Gemini API** - 大規模言語モデル
- **python-dotenv** - 環境変数管理

## ライセンス

MIT License

## 参考リンク

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [uv Documentation](https://docs.astral.sh/uv/)

