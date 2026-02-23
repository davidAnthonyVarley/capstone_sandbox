import os
import json
import pandas as pd
import glob
import numpy as np

def generate_excel_report(output_file="Experiment_Results_Final.xlsx"):
    all_summary_data = []
    
    # 1. Find all performance_data.json files recursively
    json_files = glob.glob("**/performance_data.json", recursive=True)
    
    if not json_files:
        print("No performance_data.json files found. Check your directory path!")
        return

    print(f"Processing {len(json_files)} result files...")
    all_pods = set()

    for file_path in json_files:
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                meta = data.get('test_metadata', {})
                net_data = data.get('network_performance', [])
                prom_metrics = data.get('prometheus_metrics', {})
                
                if not net_data: continue
                    
                net_perf = pd.DataFrame(net_data)
                
                # Metadata and Throughput Calculation
                size_str = str(meta.get('data_size', '0'))
                size_mib = float(size_str.replace('MB', ''))
                concurrency = int(meta.get('concurrency', 1))
                exec_sec = float(meta.get('total_execution_ms', 0)) / 1000
                throughput = (concurrency * size_mib) / exec_sec if exec_sec > 0 else 0

                entry = {
                    "Data Size": size_str,
                    "Concurrency": concurrency,
                    "Success Rate": meta.get('success_rate'),
                    "P95 Latency (ms)": net_perf['total_ms'].quantile(0.95),
                    "Throughput (MiB/s)": round(throughput, 2),
                    "Total Runtime (ms)": meta.get('total_execution_ms')
                }

                # 2. Extract P95 Memory for each Pod in this experiment
                mem_results = prom_metrics.get('memory_mb', [])
                for pod_result in mem_results:
                    pod_name = pod_result.get('metric', {}).get('pod', 'unknown')
                    # Convert Prometheus value strings to floats
                    values = [float(v[1]) for v in pod_result.get('values', [])]
                    if values:
                        p95_mem = np.percentile(values, 95)
                        entry[f"Mem_P95_{pod_name}"] = round(p95_mem, 2)
                        all_pods.add(pod_name)

                all_summary_data.append(entry)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    # 3. Organize and Sort Data
    df = pd.DataFrame(all_summary_data)
    # Use raw string r'' for regex to avoid Python 3.12+ warnings
    df['Size_Sort'] = df['Data Size'].str.extract(r'(\d+)').astype(int)
    df = df.sort_values(['Size_Sort', 'Concurrency'])
    
    # Final data for Excel (removing the sorting helper column)
    final_df = df.drop(columns=['Size_Sort'])
    
    # 4. Write to Excel and Generate Multi-Line Charts
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    final_df.to_excel(writer, sheet_name='Summary', index=False)
    
    workbook = writer.book
    summary_sheet = writer.sheets['Summary']
    chart_sheet = workbook.add_worksheet('Memory_Analysis')
    
    cols = list(final_df.columns)
    concurrency_col_idx = cols.index('Concurrency')
    
    # Group results by Data Size (1MB, 10MB, etc.)
    sizes = df['Data Size'].unique()

    for i, size in enumerate(sizes):
        size_df = df[df['Data Size'] == size]
        # Find the row range for this size in the Excel sheet
        # (Start and End are 1-based, +1 for header)
        start_row = df.index.get_loc(size_df.index[0]) + 1
        end_row = df.index.get_loc(size_df.index[-1]) + 1
        
        # CREATE THE MULTI-LINE CHART
        mem_chart = workbook.add_chart({'type': 'line'})
        
        # Add a line (series) for every pod found across all experiments
        for pod in sorted(list(all_pods)):
            col_name = f"Mem_P95_{pod}"
            if col_name in cols:
                col_idx = cols.index(col_name)
                
                mem_chart.add_series({
                    'name': pod,
                    'categories': ['Summary', start_row, concurrency_col_idx, end_row, concurrency_col_idx],
                    'values':     ['Summary', start_row, col_idx, end_row, col_idx],
                    'marker':     {'type': 'circle', 'size': 6},
                })
        
        # Chart Formatting
        mem_chart.set_title({'name': f'Memory Footprint Scaling: {size} Payloads'})
        mem_chart.set_x_axis({'name': 'Concurrent Requests'})
        mem_chart.set_y_axis({'name': '95th Percentile Memory (MiB)', 'major_gridlines': {'visible': True}})
        mem_chart.set_legend({'position': 'bottom'})
        mem_chart.set_size({'width': 800, 'height': 500})
        
        # Position charts in a column on the 'Memory_Analysis' sheet
        chart_sheet.insert_chart(f'B{2 + (i * 26)}', mem_chart)

    writer.close()
    print(f"\nReport created: {output_file}")
    print(f"Pods analyzed: {', '.join(all_pods)}")

if __name__ == "__main__":
    generate_excel_report()