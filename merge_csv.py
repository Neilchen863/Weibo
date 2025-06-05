import pandas as pd
import glob
import os

def merge_csv_files():
    # 获取所有以时间戳结尾的CSV文件（排除已存在的合并文件）
    csv_files = glob.glob('results/*_20250605_135144.csv')
    print(f'找到 {len(csv_files)} 个CSV文件：')
    
    all_dataframes = []
    total_rows = 0
    
    for file in csv_files:
        try:
            # 检查文件大小，跳过过小的文件
            file_size = os.path.getsize(file)
            if file_size < 10:  # 文件小于10字节，可能是空文件
                print(f'跳过空文件: {file} ({file_size} 字节)')
                continue
                
            df = pd.read_csv(file)
            if len(df) > 0:  # 确保有数据行
                print(f'读取 {file}: {len(df)} 行数据')
                all_dataframes.append(df)
                total_rows += len(df)
            else:
                print(f'跳过空数据文件: {file}')
                
        except Exception as e:
            print(f'读取 {file} 时出错: {e}')

    # 合并所有数据框
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # 保存合并后的文件
        output_file = 'results/combined_all_20250605_135144.csv'
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f'\n合并完成！')
        print(f'成功读取了 {len(all_dataframes)} 个CSV文件')
        print(f'总共合并了 {len(combined_df)} 行数据')
        print(f'输出文件: {output_file}')
        print(f'文件大小: {os.path.getsize(output_file)} 字节')
        
        # 显示数据统计
        if 'keyword' in combined_df.columns:
            print(f'\n关键词统计:')
            keyword_counts = combined_df['keyword'].value_counts()
            for keyword, count in keyword_counts.items():
                print(f'  {keyword}: {count} 条')
        
        return output_file
    else:
        print('没有找到有效的CSV文件进行合并')
        return None

if __name__ == "__main__":
    merge_csv_files() 