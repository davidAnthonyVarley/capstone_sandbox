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

                # CPU and Memory Extraction (Both Avg and P95)
                for metric_type in ['cpu_usage', 'memory_mb']:
                    results = prom_metrics.get(metric_type, [])
                    for pod_result in results:
                        pod_name = pod_result.get('metric', {}).get('pod', 'unknown')
                        values = [float(v[1]) for v in pod_result.get('values', [])]
                        if values:
                            if metric_type == 'cpu_usage':
                                print("we're calculating cpu metrics")
                                entry[f"CPU_Avg_{pod_name}"] = np.mean(values)
                                entry[f"CPU_P95_{pod_name}"] = np.percentile(values, 95)
                            else:
                                entry[f"Mem_Avg_{pod_name}"] = np.mean(values)
                                entry[f"Mem_P95_{pod_name}"] = np.percentile(values, 95)
                            all_pods.add(pod_name)

                all_summary_data.append(entry)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    # --- STEP 2: GROUPING & AVERAGING ---
    raw_df = pd.DataFrame(all_summary_data)
    df = raw_df.groupby(['Data Size', 'Concurrency'], as_index=False).mean()

    # Sort logically
    df['Size_Sort'] = df['Data Size'].str.extract(r'(\d+)').astype(int)
    df = df.sort_values(['Size_Sort', 'Concurrency']).drop(columns=['Size_Sort'])

    # --- STEP 3: RATE OF CHANGE CALCULATIONS ---
    analysis_frames = []
    # Identify all base metric columns
    base_metrics = [c for c in df.columns if any(x in c for x in ["CPU_Avg_", "CPU_P95_", "Mem_Avg_", "Mem_P95_"])]
    
    for size, group in df.groupby('Data Size', sort=False):
        group = group.sort_values('Concurrency')
        for col in base_metrics:
            # Rate of Change = (Y2 - Y1) / (X2 - X1)
            delta_y = group[col].diff()
            delta_x = group['Concurrency'].diff()
            group[f"Rate_{col}"] = delta_y / delta_x
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
        
        ws = workbook.add_worksheet(f'Analysis_{size}')
        indices = np.where(final_df['Data Size'] == size)[0]
        start_row, end_row = int(indices[0]) + 1, int(indices[-1]) + 1

        def create_chart(title, y_label, prefix, position):
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
                ws.insert_chart(position, chart)

        # Row 1: Memory Rates
        create_chart("Mem Avg Rate of Change", "Avg MiB/Req", "Rate_Mem_Avg_", "B2")
        create_chart("Mem P95 Rate of Change", "P95 MiB/Req", "Rate_Mem_P95_", "J2")

        # Row 2: CPU Rates
        create_chart("CPU Avg Rate of Change", "Avg Cores/Req", "Rate_CPU_Avg_", "B18")
        create_chart("CPU P95 Rate of Change", "P95 Cores/Req", "Rate_CPU_P95_", "J18")

        # Row 3: Absolute Totals
        create_chart("Absolute Memory (P95)", "Total MiB", "Mem_P95_", "B34")
        create_chart("Absolute CPU (P95)", "Total Cores", "CPU_P95_", "J34")

    writer.close()
    print(f"Report Generated with P95 Metrics: {output_file}")

if __name__ == "__main__":
    generate_excel_report()