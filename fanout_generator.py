#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Fan-Out Generator (google.genai / Gemini 専用)

要求:
- Gemini のみ
- 8分類（筆者の仮説）に厳密に準拠してサブクエリを生成
  1) 曖昧さの解消
  2) 潜在ニーズの顕在化
  3) 詳細深掘りの誘導（次の質問提案）
  4) 主張の賛否エビデンス収集
  5) エンティティ取得（人・場所・組織など）
  6) 関連性の高い文書予測
  7) セッション文脈の維持（最近の行動・状態を反映）
  8) ユーザー個別化（過去検索や位置・時間などの信号を活用）

出力:
- デフォルト: output/フォルダにCSV保存
- --json: JSON形式で標準出力（マークダウン/前置きなし）
- --csv=FILE: 指定パスにCSV保存

依存:
  pip install google-genai
環境変数:
  export GEMINI_API_KEY=xxxx

使用例:
uv run python fanout_generator.py "緑茶 健康 効果"
uv run python fanout_generator.py "EV battery recycling" --en --model=gemini-2.5-pro --n=12 --search
uv run python fanout_generator.py "緑茶 健康 効果" --csv=custom.csv
uv run python fanout_generator.py "緑茶 健康 効果" --json

オプション:
  --ja / --en  : 出力言語（省略時はシードから自動判定）
  --n=INT      : 各カテゴリの最大件数
  --model=...  : モデル名（既定: gemini-2.5-flash）
  --search     : Google 検索ツールを有効化（引用/探索強化が必要なとき）
  --csv=FILE   : CSV形式でエクスポート（seed,locale,category,subquery）
  --json       : JSON形式で標準出力（CSV保存しない）

"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ------------------------------
# Helpers
# ------------------------------

def is_japanese(text: str) -> bool:
    return bool(re.search(r"[぀-ヿ㐀-䶿一-鿿]", text))


# ------------------------------
# Prompt (8分類チューニング)
# ------------------------------

def build_prompt(seed: str, locale: str, max_per_category: int) -> str:
    lang = "日本語" if locale == "ja" else "English"
    # 各カテゴリの定義と生成ルールを明示し、LLMの出力を安定化
    return f"""
あなたは検索クエリ設計の専門家です。以下の8分類に基づき、シードから多様で重複のない**サブクエリ**を生成してください。出力は**JSONのみ**（マークダウンや説明文は禁止）。言語は{lang}。

【カテゴリ（固定の日本語キー）と狙い】
1) 曖昧さの解消: 多義語や同名語の意味・文脈を切り分ける。
2) 潜在ニーズの顕在化: 潜在課題・目的に対応した観点を広げる。
3) 詳細深掘りの誘導（次の質問提案）: 次に聞くべき具体的フォローアップを提示。
4) 主張の賛否エビデンス収集: 賛成/反対の根拠・エビデンス・反証を探索。
5) エンティティ取得（人・場所・組織など）: 関連する固有名詞や属性を列挙。
6) 関連性の高い文書予測: 高関連のトピック/文書タイプ/資料を推定。
7) セッション文脈の維持（最近の行動・状態を反映）: 現在の作業文脈やタスク進行を踏まえたクエリ。
8) ユーザー個別化（過去検索や位置・時間などの信号を活用）: セグメント/地域/時間/履歴で差が出る切り口。

【生成ルール】
- 各カテゴリ 最大 {max_per_category} 件。
- 各サブクエリは query fan-out で派生した検索キーワードとして短い名詞句または命令形で表現し、文や説明は書かない。
- 1クエリ 6〜16語 / 12〜40字 程度で**具体・可動的**に（名詞列よりも動作/条件を入れる）。
- 重複・言い換えを避け、多様な意図（how/compare/risk/cost/policy/benchmark/地域/時期）をカバー。
- 記号は最小限、引用符/絵文字/不要な句読点は使用禁止。
- シードの語をそのまま繰り返しすぎない（同義語・上位下位語を混ぜる）。

【出力形式（JSONのみ）】
{{
  "seed": "{seed}",
  "locale": "{locale}",
  "categories": {{
    "曖昧さの解消": ["..."],
    "潜在ニーズの顕在化": ["..."],
    "詳細深掘りの誘導（次の質問提案）": ["..."],
    "主張の賛否エビデンス収集": ["..."],
    "エンティティ取得（人・場所・組織など）": ["..."],
    "関連性の高い文書予測": ["..."],
    "セッション文脈の維持（最近の行動・状態を反映）": ["..."],
    "ユーザー個別化（過去検索や位置・時間などの信号を活用）": ["..."]
  }}
}}
※各カテゴリ配列の要素は query fan-out で派生した検索キーワードのみ。

シード: "{seed}"
""".strip()


# ------------------------------
# JSON Schema (日本語キー固定)
# ------------------------------

def categories_schema() -> Dict:
    def arr():
        return {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "properties": {
            "seed": {"type": "string"},
            "locale": {"type": "string"},
            "categories": {
                "type": "object",
                "properties": {
                    "曖昧さの解消": arr(),
                    "潜在ニーズの顕在化": arr(),
                    "詳細深掘りの誘導（次の質問提案）": arr(),
                    "主張の賛否エビデンス収集": arr(),
                    "エンティティ取得（人・場所・組織など）": arr(),
                    "関連性の高い文書予測": arr(),
                    "セッション文脈の維持（最近の行動・状態を反映）": arr(),
                    "ユーザー個別化（過去検索や位置・時間などの信号を活用）": arr(),
                },
                "required": [
                    "曖昧さの解消",
                    "潜在ニーズの顕在化",
                    "詳細深掘りの誘導（次の質問提案）",
                    "主張の賛否エビデンス収集",
                    "エンティティ取得（人・場所・組織など）",
                    "関連性の高い文書予測",
                    "セッション文脈の維持（最近の行動・状態を反映）",
                    "ユーザー個別化（過去検索や位置・時間などの信号を活用）",
                ],
                "additionalProperties": False,
            },
        },
        "required": ["seed", "locale", "categories"],
        "additionalProperties": False,
    }


# ------------------------------
# google.genai 呼び出し
# ------------------------------

def generate_fanout_google_genai(seed: str, locale: Optional[str] = None, max_per_category: int = 8, model_name: str = "gemini-2.5-flash", enable_search: bool = False) -> Dict[str, List[str]]:
    seed = seed.strip()
    if not seed:
        raise ValueError("Seed keyword must be non-empty")
    if locale is None:
        locale = 'ja' if is_japanese(seed) else 'en'

    try:
        from google import genai
        from google.genai import types
    except Exception as e:
        raise RuntimeError("google-genai is not installed. Run: pip install google-genai") from e

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # Safety settings（必要に応じて調整）
    safety = [
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_LOW_AND_ABOVE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_LOW_AND_ABOVE"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_LOW_AND_ABOVE"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_LOW_AND_ABOVE"),
    ]

    # Optional GoogleSearch tool
    tools = [types.Tool(googleSearch=types.GoogleSearch())] if enable_search else None

    cfg = types.GenerateContentConfig(
        response_mime_type="application/json",
        #response_schema=categories_schema(),
        temperature=0.3,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        safety_settings=safety,
        tools=tools,
    )

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=build_prompt(seed, locale, max_per_category))])
    ]

    text = ""
    for chunk in client.models.generate_content_stream(model=model_name, contents=contents, config=cfg):
        if getattr(chunk, "text", None):
            text += chunk.text

    try:
        data = json.loads(text)
        return data["categories"]
    except Exception:
        return {"Raw": [text]}


# ------------------------------
# CSV Export
# ------------------------------

def export_to_csv(seed: str, locale: str, categories: Dict[str, List[str]], filepath: str) -> None:
    """
    Export fanout results to CSV format.
    Format: seed,locale,category,subquery (one row per subquery)
    """
    import csv
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['seed', 'locale', 'category', 'subquery'])
        # Write data rows
        for category, queries in categories.items():
            for query in queries:
                writer.writerow([seed, locale, category, query])


# ------------------------------
# CLI
# ------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fanout_generator.py '<seed>' [--ja|--en] [--n=8] [--model=gemini-2.5-flash] [--search] [--csv=FILE] [--json]")
        sys.exit(1)

    seed = sys.argv[1]
    locale: Optional[str] = None
    max_n = 8
    model_name = "gemini-2.5-flash"
    enable_search = False
    csv_output: Optional[str] = None
    json_only = False

    for arg in sys.argv[2:]:
        if arg == "--ja":
            locale = 'ja'
        elif arg == "--en":
            locale = 'en'
        elif arg.startswith("--n="):
            try:
                max_n = int(arg.split("=", 1)[1])
            except Exception:
                pass
        elif arg.startswith("--model="):
            model_name = arg.split("=", 1)[1]
        elif arg == "--search":
            enable_search = True
        elif arg.startswith("--csv="):
            csv_output = arg.split("=", 1)[1]
        elif arg == "--json":
            json_only = True

    locale = locale or ('ja' if is_japanese(seed) else 'en')

    cats = generate_fanout_google_genai(
        seed,
        locale=locale,
        max_per_category=max_n,
        model_name=model_name,
        enable_search=enable_search,
    )

    # Output: JSON only, CSV to custom path, or CSV to output/ (default)
    if json_only:
        # JSON to stdout
        print(json.dumps({
            "seed": seed,
            "locale": locale,
            "categories": cats
        }, ensure_ascii=False, indent=2))
    else:
        # CSV export
        if csv_output is None:
            # Default: save to output/ folder
            Path("output").mkdir(parents=True, exist_ok=True)
            safe_seed = re.sub(r'[<>:"/\\|?*]', '', seed.replace(" ", "_"))[:50]
            csv_output = f"output/{safe_seed}_fanout.csv"

        export_to_csv(seed, locale, cats, csv_output)
        print(f"CSV exported to: {csv_output}")
