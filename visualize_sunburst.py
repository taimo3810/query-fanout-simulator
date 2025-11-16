#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Fan-Out Sunburst Visualization
PlotlyでCSVデータをSunburst ChartのPNG画像として保存
デフォルト出力先: output/フォルダ

使用例:
  uv run python visualize_sunburst.py output/seed_fanout.csv
  uv run python visualize_sunburst.py output/seed_fanout.csv --output=chart.png
  uv run python visualize_sunburst.py output/seed_fanout.csv --width=2000 --height=2000
"""
import csv
import sys
from pathlib import Path
from typing import List, Dict, Optional
import plotly.graph_objects as go
import plotly.express as px


# 8カテゴリの色設定（視認性重視・鮮やかな配色）
CATEGORY_COLORS = {
    "曖昧さの解消": "#E74C3C",  # 鮮やかな赤
    "潜在ニーズの顕在化": "#1ABC9C",  # エメラルドグリーン
    "詳細深掘りの誘導（次の質問提案）": "#3498DB",  # 鮮やかな青
    "主張の賛否エビデンス収集": "#E67E22",  # 鮮やかなオレンジ
    "エンティティ取得（人・場所・組織など）": "#2ECC71",  # 鮮やかなグリーン
    "関連性の高い文書予測": "#F39C12",  # ゴールデンイエロー
    "セッション文脈の維持（最近の行動・状態を反映）": "#9B59B6",  # 鮮やかなパープル
    "ユーザー個別化（過去検索や位置・時間などの信号を活用）": "#E91E63",  # ピンク
}


def load_csv_data(filepath: str) -> List[Dict[str, str]]:
    """CSVファイルを読み込む"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def create_sunburst_data(csv_data: List[Dict[str, str]]) -> tuple:
    """
    CSVデータからSunburst Chart用のデータ構造を作成

    Returns:
        (labels, parents, values, colors, hover_text)
    """
    if not csv_data:
        raise ValueError("CSV data is empty")

    seed = csv_data[0]['seed']
    locale = csv_data[0]['locale']

    # カテゴリごとにグループ化
    categories: Dict[str, List[str]] = {}
    for row in csv_data:
        cat = row['category']
        subq = row['subquery']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(subq)

    # デバッグ情報
    total_subqueries = sum(len(queries) for queries in categories.values())
    print(f"📊 データ読み込み完了:")
    print(f"  - カテゴリ数: {len(categories)}")
    print(f"  - サブクエリ総数: {total_subqueries}")
    print(f"  - シード: {seed}")

    labels = [seed]  # ルート
    parents = [""]  # ルートの親は空文字列
    values = [total_subqueries]  # ルートの値は全サブクエリの合計
    colors = ["#E8E8E8"]  # ルートは薄いグレー（背景と区別できる）
    hover_text = [f"<b>{seed}</b><br>全{total_subqueries}件のサブクエリ"]

    # カテゴリとサブクエリを追加
    for category, subqueries in categories.items():
        # カテゴリノード
        labels.append(category)
        parents.append(seed)
        values.append(len(subqueries))
        colors.append(CATEGORY_COLORS.get(category, "#CCCCCC"))
        hover_text.append(f"<b>{category}</b><br>サブクエリ数: {len(subqueries)}")

        # サブクエリノード
        for subquery in subqueries:
            labels.append(subquery)
            parents.append(category)
            values.append(1)
            colors.append(CATEGORY_COLORS.get(category, "#CCCCCC"))
            hover_text.append(f"{subquery}")

    print(f"  - 生成ノード数: {len(labels)}")

    return labels, parents, values, colors, hover_text


def create_sunburst_chart(
    csv_filepath: str,
    output_filepath: str,
    width: int = 2000,
    height: int = 2000
) -> go.Figure:
    """
    Sunburst ChartをPNG画像として生成・保存

    Args:
        csv_filepath: 入力CSVファイルパス
        output_filepath: 出力PNGファイルパス
        width: チャートの幅（px）
        height: チャートの高さ（px）

    Returns:
        Plotly Figure オブジェクト
    """
    csv_data = load_csv_data(csv_filepath)
    labels, parents, values, colors, hover_text = create_sunburst_data(csv_data)

    seed = csv_data[0]['seed']

    # Sunburst Chart作成
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(color='white', width=3)  # 境界線を太く
        ),
        hovertemplate='<b>%{label}</b><br>%{customdata}<extra></extra>',
        customdata=hover_text,
        branchvalues="total",
        textfont=dict(
            size=14,  # フォントサイズ拡大
            family="sans-serif",
            color="#333"  # テキスト色を濃く
        ),
        insidetextorientation='radial',  # テキストを放射状に配置
    ))

    # レイアウト設定
    fig.update_layout(
        title=dict(
            text=f"Query Fan-Out: {seed}",
            font=dict(size=32, family="sans-serif", color="#2C3E50", weight=600),  # タイトルを大きく
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        width=width,
        height=height,
        margin=dict(t=120, l=20, r=20, b=20),  # マージン調整
        paper_bgcolor='#FFFFFF',  # 背景を純白に
        font=dict(family="sans-serif", size=13),  # ベースフォントサイズ拡大
    )

    # PNG画像として保存
    fig.write_image(output_filepath, format='png', width=width, height=height)
    print(f"🖼️  PNG saved to: {output_filepath} ({width}x{height}px)")

    return fig


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_sunburst.py <csv_file> [--output=FILE.png] [--width=1000] [--height=1000]")
        print("\nExample:")
        print("  python visualize_sunburst.py output.csv")
        print("  python visualize_sunburst.py output.csv --output=chart.png")
        print("  python visualize_sunburst.py output.csv --width=2000 --height=2000")
        sys.exit(1)

    csv_file = sys.argv[1]
    output_file = None
    width = 1000
    height = 1000

    # オプション解析
    for arg in sys.argv[2:]:
        if arg.startswith("--output="):
            output_file = arg.split("=", 1)[1]
        elif arg.startswith("--width="):
            width = int(arg.split("=", 1)[1])
        elif arg.startswith("--height="):
            height = int(arg.split("=", 1)[1])

    # デフォルト出力ファイル名（output/フォルダに保存）
    if output_file is None:
        csv_path = Path(csv_file)
        # output/フォルダに保存
        Path("output").mkdir(parents=True, exist_ok=True)
        output_file = f"output/{csv_path.stem.replace('_fanout', '')}_sunburst.png"

    # Sunburst Chart生成（PNG画像として保存）
    create_sunburst_chart(
        csv_filepath=csv_file,
        output_filepath=output_file,
        width=width,
        height=height
    )


if __name__ == "__main__":
    main()
