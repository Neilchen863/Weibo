import pandas as pd
import os

input_csv = 'results/all_results_20250619_123847.csv'
output_csv = 'results/filtered_results_20250619_123847.csv'

def filter_has_video(input_csv, output_csv):
    df = pd.read_csv(input_csv, encoding='utf-8')
    # 清理 video_url 字段
    df['video_url'] = df['video_url'].fillna('').astype(str).str.strip()
    # 只保留 video_url 有效的行
    filtered = df[
        (df['video_url'] != '') &
        (df['video_url'].str.lower() != 'nan') &
        (df['video_url'].str.lower() != 'none') &
        (df['video_url'].str.startswith('http'))
    ].copy()
    filtered.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f'已保存只包含有视频的微博到: {output_csv}，共 {len(filtered)} 条')

if __name__ == '__main__':
    filter_has_video(input_csv, output_csv) 