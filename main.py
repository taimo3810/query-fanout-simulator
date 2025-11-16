#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Fan-Out Simulator - Main Entry Point
シードクエリからサブクエリ生成 → Sunburst Chart可視化を一気通貫で実行

使用例:
  uv run python main.py "緑茶 健康 効果"
  uv run python main.py "EV battery recycling" --en --n=12 --width=2000 --height=2000
  uv run python main.py "AI ethics" --model=gemini-2.5-pro --search
"""
import os
import sys
import re
from pathlib import Path
from typing import Optional

# 既存モジュールをインポート
from fanout_generator import generate_fanout_google_genai, export_to_csv, is_japanese
from visualize_sunburst import create_sunburst_chart


def sanitize_filename(text: str) -> str:
    """
    ファイル名として安全な文字列に変換
    スペースをアンダースコアに、使えない文字を削除
    """
    # スペースをアンダースコアに
    text = text.replace(" ", "_")
    # ファイル名に使えない文字を削除
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    # 長さ制限（最大50文字）
    if len(text) > 50:
        text = text[:50]
    return text


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py '<seed_query>' [options]")
        print("\nOptions:")
        print("  --ja / --en          : Output language (auto-detect if not specified)")
        print("  --n=INT              : Max subqueries per category (default: 8)")
        print("  --model=MODEL        : Gemini model name (default: gemini-2.5-flash)")
        print("  --search             : Enable Google Search tool")
        print("  --width=INT          : Chart width in pixels (default: 2000)")
        print("  --height=INT         : Chart height in pixels (default: 2000)")
        print("  --output-dir=DIR     : Output directory (default: output)")
        print("\nExample:")
        print("  python main.py '緑茶 健康 効果'")
        print("  python main.py 'EV battery recycling' --en --n=12 --width=2000 --height=2000")
        sys.exit(1)

    seed = sys.argv[1]

    # オプション解析
    locale: Optional[str] = None
    max_n = 8
    model_name = "gemini-2.5-flash"
    enable_search = False
    width = 2000  # デフォルトを高解像度に
    height = 2000
    output_dir = "output"

    for arg in sys.argv[2:]:
        if arg == "--ja":
            locale = 'ja'
        elif arg == "--en":
            locale = 'en'
        elif arg.startswith("--n="):
            try:
                max_n = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif arg.startswith("--model="):
            model_name = arg.split("=", 1)[1]
        elif arg == "--search":
            enable_search = True
        elif arg.startswith("--width="):
            try:
                width = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif arg.startswith("--height="):
            try:
                height = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif arg.startswith("--output-dir="):
            output_dir = arg.split("=", 1)[1]

    # ロケール自動判定
    if locale is None:
        locale = 'ja' if is_japanese(seed) else 'en'

    # 出力ディレクトリ作成
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ファイル名用のseed文字列
    safe_seed = sanitize_filename(seed)
    csv_path = os.path.join(output_dir, f"{safe_seed}_fanout.csv")
    png_path = os.path.join(output_dir, f"{safe_seed}_sunburst.png")

    print("=" * 60)
    print("🚀 Query Fan-Out Simulator")
    print("=" * 60)
    print(f"Seed Query: {seed}")
    print(f"Locale: {locale}")
    print(f"Model: {model_name}")
    print(f"Max per category: {max_n}")
    print(f"Chart size: {width}x{height}px")
    print(f"Output directory: {output_dir}/")
    print("=" * 60)

    # ステップ1: Query Fan-Out生成
    print("\n[1/2] 🔍 Generating query fan-out...")
    try:
        categories = generate_fanout_google_genai(
            seed,
            locale=locale,
            max_per_category=max_n,
            model_name=model_name,
            enable_search=enable_search,
        )

        # CSV保存
        export_to_csv(seed, locale, categories, csv_path)
        print(f"✅ CSV saved to: {csv_path}")

    except Exception as e:
        print(f"❌ Error generating fan-out: {e}")
        sys.exit(1)

    # ステップ2: Sunburst Chart生成
    print("\n[2/2] 🎨 Generating Sunburst Chart...")
    try:
        create_sunburst_chart(
            csv_filepath=csv_path,
            output_filepath=png_path,
            width=width,
            height=height
        )
    except Exception as e:
        print(f"❌ Error generating chart: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✨ Complete!")
    print("=" * 60)
    print(f"📄 CSV: {csv_path}")
    print(f"🖼️  PNG: {png_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
