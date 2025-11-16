# Query Fan-Out Simulator

検索クエリから多角的なサブクエリを自動生成し、美しいSunburst Chartで可視化するツール。

## 概要

Query Fan-Out Simulatorは、1つのシードクエリから8つの異なる観点でサブクエリを生成し、視覚的に分かりやすいSunburst Chart（放射状円グラフ）として可視化します。Google検索のQuery Fan-Outの仕組みを理解・実験するために開発されました。

### 8つのカテゴリ

1. **曖昧さの解消** - 多義語や同名語の意味・文脈を切り分ける
2. **潜在ニーズの顕在化** - 潜在課題・目的に対応した観点を広げる
3. **詳細深掘りの誘導** - 次に聞くべき具体的フォローアップを提示
4. **主張の賛否エビデンス収集** - 賛成/反対の根拠・エビデンス・反証を探索
5. **エンティティ取得** - 関連する人・場所・組織などの固有名詞を列挙
6. **関連性の高い文書予測** - 高関連のトピック/文書タイプ/資料を推定
7. **セッション文脈の維持** - 現在の作業文脈やタスク進行を踏まえたクエリ
8. **ユーザー個別化** - セグメント/地域/時間/履歴で差が出る切り口

### 主な機能

- **AI駆動のサブクエリ生成** - Google Gemini APIを使用した高品質な生成
- **美しいビジュアライゼーション** - 2000x2000px高解像度Sunburst Chart
- **一気通貫ワークフロー** - 生成から可視化まで1コマンドで完結
- **CSV出力対応** - データ分析やカスタマイズに対応
- **多言語対応** - 日本語・英語（自動判定またはオプション指定）

## 🛠️ システム要件

- **Python**: 3.12 以上
- **パッケージマネージャ**: [uv](https://github.com/astral-sh/uv)（推奨）
- **API Key**: [Google Gemini API](https://ai.google.dev/)

## 環境構築

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/query-fanout-simulator.git
cd query-fanout-simulator
```

### 2. 依存関係のインストール

```bash
uv sync
```

### 3. API Keyの設定

Gemini API Keyを環境変数に設定します：

```bash
export GEMINI_API_KEY="your_api_key_here"
```

または、`.env`ファイルに記述：

```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## Get Started

### 基本的な使い方（推奨）

main.pyを使用して、サブクエリ生成とビジュアライゼーションを一気に実行：

```bash
uv run python main.py "緑茶 健康 効果"
```

出力:
```
output/
  ├── 緑茶_健康_効果_fanout.csv      # サブクエリデータ（CSV）
  └── 緑茶_健康_効果_sunburst.png    # ビジュアライゼーション（PNG）
```

### オプション指定

```bash
# 英語クエリで生成
uv run python main.py "AI ethics" --en

# カテゴリあたりのサブクエリ数を増やす
uv run python main.py "コーヒー 健康" --n=12

# 高解像度画像生成
uv run python main.py "気候変動" --width=3000 --height=3000

# 高性能モデルを使用
uv run python main.py "量子コンピュータ" --model=gemini-2.5-pro

# Google検索ツールを有効化
uv run python main.py "最新AI技術" --search
```

### 個別実行

#### 1. サブクエリ生成のみ

```bash
uv run python fanout_generator.py "緑茶 健康 効果"

# JSON形式で出力
uv run python fanout_generator.py "緑茶 健康 効果" --json
```

#### 2. ビジュアライゼーションのみ

```bash
uv run python visualize_sunburst.py output/緑茶_健康_効果_fanout.csv

# カスタムサイズ
uv run python visualize_sunburst.py output/緑茶_健康_効果_fanout.csv --width=4000 --height=4000
```

## 📁 ファイル構成

```
query-fanout-simulator/
├── main.py                    # メインエントリポイント（一気通貫実行）
├── fanout_generator.py        # サブクエリ生成スクリプト
├── visualize_sunburst.py      # Sunburst Chart生成スクリプト
├── output/                    # 出力ディレクトリ（自動生成）
│   ├── *_fanout.csv          # 生成されたサブクエリ（CSV）
│   └── *_sunburst.png        # 可視化画像（PNG）
├── pyproject.toml             # プロジェクト設定・依存関係
├── uv.lock                    # 依存関係ロックファイル
└── README.md                  # このファイル
```

### 各スクリプトの役割

- **main.py**: サブクエリ生成 → ビジュアライゼーションを自動実行
- **fanout_generator.py**: Gemini APIを使用してサブクエリを生成
- **visualize_sunburst.py**: CSVデータからSunburst Chart（PNG）を生成

## 出力形式

### CSV形式

```csv
seed,locale,category,subquery
緑茶 健康 効果,ja,曖昧さの解消,緑茶 種類別 健康効能 比較
緑茶 健康 効果,ja,曖昧さの解消,カテキン含有量 違い 健康影響
...
```

### PNG画像

- **デフォルトサイズ**: 2000x2000px（高解像度）
- **形式**: PNG（ブログ・プレゼンテーション向け）
- **カラーパレット**: 8色の鮮やかな配色（視認性重視）

## ⚙️ オプション一覧

### main.py

| オプション | 説明 | デフォルト |
|----------|------|-----------|
| `--ja` / `--en` | 出力言語（自動判定も可） | 自動判定 |
| `--n=INT` | カテゴリあたりの最大サブクエリ数 | 8 |
| `--model=MODEL` | Geminiモデル名 | gemini-2.5-flash |
| `--search` | Google検索ツールを有効化 | 無効 |
| `--width=INT` | 画像幅（px） | 2000 |
| `--height=INT` | 画像高さ（px） | 2000 |
| `--output-dir=DIR` | 出力ディレクトリ | output |

### fanout_generator.py

| オプション | 説明 | デフォルト |
|----------|------|-----------|
| `--ja` / `--en` | 出力言語 | 自動判定 |
| `--n=INT` | カテゴリあたりの最大サブクエリ数 | 8 |
| `--model=MODEL` | Geminiモデル名 | gemini-2.5-flash |
| `--search` | Google検索ツールを有効化 | 無効 |
| `--csv=FILE` | CSV出力先（カスタムパス） | output/{seed}_fanout.csv |
| `--json` | JSON形式で標準出力 | CSV出力 |

### visualize_sunburst.py

| オプション | 説明 | デフォルト |
|----------|------|-----------|
| `--output=FILE` | PNG出力先（カスタムパス） | output/{seed}_sunburst.png |
| `--width=INT` | 画像幅（px） | 2000 |
| `--height=INT` | 画像高さ（px） | 2000 |

## カスタマイズ

### モデルの選択

Geminiのモデルを切り替えて生成品質を調整：

```bash
# Flash（高速・低コスト）
uv run python main.py "クエリ" --model=gemini-2.5-flash

# Pro（高品質・やや遅い）
uv run python main.py "クエリ" --model=gemini-2.5-pro
```

### 色のカスタマイズ

`visualize_sunburst.py`の`CATEGORY_COLORS`辞書を編集：

```python
CATEGORY_COLORS = {
    "曖昧さの解消": "#YOUR_COLOR_HERE",
    ...
}
```
