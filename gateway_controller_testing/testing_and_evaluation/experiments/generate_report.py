import os
import json
import pandas as pd
import glob
import numpy as np

def generate_excel_report(output_file="Experiment_Results_Final.xlsx"):
    all_summary_data = []
    json_files = glob.glob("**/performance_data.json", recursive=True)
    
    if not json_files:
        print("No performance_data.json files found.")
        return

    print(f"Processing {len(json_files)} result files...")
    all_pods = set()

    # --- STEP 1: DATA EXTRACTION ---
    for file_path in json_files:
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                meta = data.get('test_metadata', {})
                prom_metrics = data.get('prometheus_metrics', {})
                
                size_str = str(meta.get('data_size', '0'))
                concurrency = int(meta.get('concurrency', 1))
                
                entry = {
                    "Data Size": size_str,
                    "Concurrency": concurrency
                }

                # CPU and Memory Extraction
                for metric_type in ['cpu_usage', 'memory_mb']:
                    results = prom_metrics.get(metric_type, [])
                    for pod_result in results:
                        pod_name = pod_result.get('metric', {}).get('pod', 'unknown')
                        values = [float(v[1]) for v in pod_result.get('values', [])]
                        if values:
                            if metric_type == 'cpu_usage':
                                entry[f"CPU_Avg_{pod_name}"] = np.mean(values)
                            else:
                                entry[f"Mem_Avg_{pod_name}"] = np.mean(values)
                            all_pods.add(pod_name)

                all_summary_data.append(entry)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    # --- STEP 2: GROUPING & AVERAGING ---
    raw_df = pd.DataFrame(all_summary_data)
    # Average all rows with same Size/Concurrency
    df = raw_df.groupby(['Data Size', 'Concurrency'], as_index=False).mean()

    # Sort logically
    df['Size_Sort'] = df['Data Size'].str.extract(r'(\d+)').astype(int)
    df = df.sort_values(['Size_Sort', 'Concurrency']).drop(columns=['Size_Sort'])

    # --- STEP 3: MATHEMATICAL RATE OF CHANGE (SLOPE) ---
    analysis_frames = []
    pod_metrics = [c for c in df.columns if "CPU_Avg_" in c or "Mem_Avg_" in c]
    
    for size, group in df.groupby('Data Size', sort=False):
        group = group.sort_values('Concurrency')
        for col in pod_metrics:
            # Rate of Change = (Y2 - Y1) / (X2 - X1)
            delta_y = group[col].diff()
            delta_x = group['Concurrency'].diff()
            group[f"Rate_{col}"] = delta_y / delta_x
            # "Change from last" (Simple difference)
            group[f"Diff_{col}"] = delta_y
        analysis_frames.append(group)
    
    final_df = pd.concat(analysis_frames).reset_index(drop=True)

    # --- STEP 4: EXCEL GENERATION & CHARTING ---
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    final_df.to_excel(writer, sheet_name='Summary', index=False)
    workbook = writer.book
    
    target_sizes = ['1MB', '10MB', '100MB']
    cols = list(final_df.columns)
    conc_idx = cols.index('Concurrency')

    for size in target_sizes:
        if size not in final_df['Data Size'].values: continue
        
        sheet_name = f'Analysis_{size}'
        ws = workbook.add_worksheet(sheet_name)
        indices = np.where(final_df['Data Size'] == size)[0]
        start_row, end_row = int(indices[0]) + 1, int(indices[-1]) + 1

        def create_chart(title, y_label, prefix):
            chart = workbook.add_chart({'type': 'scatter', 'subtype': 'straight_with_markers'})
            has_data = False
            for pod in sorted(list(all_pods)):
                col_name = f"{prefix}{pod}"
                if col_name in cols:
                    chart.add_series({
                        'name': pod,
                        'categories': ['Summary', start_row, conc_idx, end_row, conc_idx],
                        'values':     ['Summary', start_row, cols.index(col_name), end_row, cols.index(col_name)],
                    })
                    has_data = True
            if has_data:
                chart.set_title({'name': f'{title} ({size})'})
                chart.set_x_axis({'name': 'Concurrency'})
                chart.set_y_axis({'name': y_label})
                return chart
            return None

        # 1. Chart: Rate of Change - Memory (The Slope)
        c1 = create_chart("Memory Rate of Change", "MiB per extra Req", "Rate_Mem_Avg_")
        if c1: ws.insert_chart('B2', c1)

        # 2. Chart: Rate of Change - CPU (The Slope)
        c2 = create_chart("CPU Rate of Change", "Cores per extra Req", "Rate_CPU_Avg_")
        if c2: ws.insert_chart('J2', c2)

        # 3. Chart: Absolute Memory Usage (Comparison)
        c3 = create_chart("Absolute Memory Usage", "Total MiB", "Mem_Avg_")
        if c3: ws.insert_chart('B18', c3)

        # 4. Chart: Change in Memory (Difference from last step)
        c4 = create_chart("Step-over-Step Memory Change", "Delta MiB", "Diff_Mem_Avg_")
        if c4: ws.insert_chart('J18', c4)

    writer.close()
    print(f"Report Generated: {output_file}")

if __name__ == "__main__":
    generate_excel_report()