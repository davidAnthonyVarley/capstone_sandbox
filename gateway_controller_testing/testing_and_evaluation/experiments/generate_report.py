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

    for file_path in json_files:
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                meta = data.get('test_metadata', {})
                prom_metrics = data.get('prometheus_metrics', {})
                net_data = data.get('network_performance', []) #
                
                size_str = str(meta.get('data_size', '0'))
                concurrency = int(meta.get('concurrency', 1))
                
                entry = {
                    "Data Size": size_str,
                    "Concurrency": concurrency
                }

                # --- STEP 1: NETWORK LATENCY EXTRACTION ---
                if net_data:
                    net_df = pd.DataFrame(net_data)
                    # Metrics: conn_ms, ttfb_ms, total_ms
                    for metric in ['conn_ms', 'ttfb_ms', 'total_ms']:
                        entry[f"Net_Avg_{metric}"] = net_df[metric].mean()
                        entry[f"Net_P95_{metric}"] = net_df[metric].quantile(0.95)

                # --- STEP 2: POD METRICS EXTRACTION ---
                for metric_type in ['cpu_usage', 'memory_mb']:
                    results = prom_metrics.get(metric_type, [])
                    for pod_result in results:
                        pod_name = pod_result.get('metric', {}).get('pod', 'unknown')
                        values = [float(v[1]) for v in pod_result.get('values', [])]
                        if values:
                            if metric_type == 'cpu_usage':
                                entry[f"CPU_Avg_{pod_name}"] = np.mean(values)
                                entry[f"CPU_P95_{pod_name}"] = np.percentile(values, 95)
                            else:
                                entry[f"Mem_Avg_{pod_name}"] = np.mean(values)
                                entry[f"Mem_P95_{pod_name}"] = np.percentile(values, 95)
                            all_pods.add(pod_name)

                all_summary_data.append(entry)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    # --- STEP 3: GROUPING & AVERAGING ---
    raw_df = pd.DataFrame(all_summary_data)
    df = raw_df.groupby(['Data Size', 'Concurrency'], as_index=False).mean()
    
    # Sort logically
    df['Size_Sort'] = df['Data Size'].str.extract(r'(\d+)').astype(int)
    df = df.sort_values(['Size_Sort', 'Concurrency']).drop(columns=['Size_Sort'])

    # --- STEP 4: RATE OF GROWTH CALCULATIONS ---
    analysis_frames = []
    # Include both Pod metrics and Network metrics in Rate calculations
    base_metrics = [c for c in df.columns if any(x in c for x in ["CPU_", "Mem_", "Net_"])]
    
    for size, group in df.groupby('Data Size', sort=False):
        group = group.sort_values('Concurrency')
        for col in base_metrics:
            delta_y = group[col].diff()
            delta_x = group['Concurrency'].diff()
            group[f"Rate_{col}"] = delta_y / delta_x
        analysis_frames.append(group)
    
    final_df = pd.concat(analysis_frames).reset_index(drop=True)

    # --- STEP 5: EXCEL GENERATION ---
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

        def create_chart(title, y_label, series_prefixes, position):
            chart = workbook.add_chart({'type': 'scatter', 'subtype': 'straight_with_markers'})
            has_data = False
            
            # This handles both pod-specific series and general network series
            for prefix in series_prefixes:
                # If prefix is for pod metrics
                if any(x in prefix for x in ["CPU_", "Mem_"]):
                    for pod in sorted(list(all_pods)):
                        col_name = f"{prefix}{pod}"
                        if col_name in cols:
                            chart.add_series({
                                'name': pod,
                                'categories': ['Summary', start_row, conc_idx, end_row, conc_idx],
                                'values':     ['Summary', start_row, cols.index(col_name), end_row, cols.index(col_name)],
                            })
                            has_data = True
                # If prefix is for network metrics
                else:
                    if prefix in cols:
                        chart.add_series({
                            'name': prefix.replace("Net_Avg_", "").replace("Net_P95_", "P95 "),
                            'categories': ['Summary', start_row, conc_idx, end_row, conc_idx],
                            'values':     ['Summary', start_row, cols.index(prefix), end_row, cols.index(prefix)],
                        })
                        has_data = True

            if has_data:
                chart.set_title({'name': f'{title} ({size})'})
                chart.set_x_axis({'name': 'Concurrency'})
                chart.set_y_axis({'name': y_label})
                ws.insert_chart(position, chart)

        # --- NEW LATENCY CHARTS ---
        # 1. Absolute P95 Latencies
        create_chart("P95 Latency Scaling", "Time (ms)", 
                     ["Net_P95_conn_ms", "Net_P95_ttfb_ms", "Net_P95_total_ms"], "B2")
        
        # 2. Rate of Growth for Total Latency
        create_chart("Total Latency Growth Rate", "ms per extra Req", 
                     ["Rate_Net_Avg_total_ms", "Rate_Net_P95_total_ms"], "J2")

        # --- POD RESOURCE CHARTS (Existing) ---
        create_chart("Mem P95 Rate of Change", "P95 MiB/Req", ["Rate_Mem_P95_"], "B18")
        create_chart("CPU P95 Rate of Change", "P95 Cores/Req", ["Rate_CPU_P95_"], "J18")

        create_chart(
            title="Absolute Average CPU Usage", 
            y_label="Total Cores", 
            series_prefixes=["CPU_Avg_"], 
            position="B50"
        )
        
        # 2. Average CPU Rate of Change
        # Shows the CPU cost in "Cores per Request" for each pod.
        create_chart(
            title="Average CPU Rate of Change", 
            y_label="Cores per extra Req", 
            series_prefixes=["Rate_CPU_Avg_"], 
            position="J50"
        )

        # --- LATENCY ANALYSIS CHARTS ---
        # 1. Absolute Average Latency Metrics
        # Compares Avg Conn, TTFB, and Total Latency on one chart.
        create_chart(
            title="Average Latency Scaling", 
            y_label="Time (ms)", 
            series_prefixes=["Net_Avg_conn_ms", "Net_Avg_ttfb_ms", "Net_Avg_total_ms"], 
            position="B66"
        )
        
        # 2. Average Latency Rate of Change
        # Shows the growth in latency (ms) for every additional concurrent request.
        create_chart(
            title="Avg Latency Growth Rate", 
            y_label="ms per extra Req", 
            series_prefixes=["Rate_Net_Avg_conn_ms", "Rate_Net_Avg_ttfb_ms", "Rate_Net_Avg_total_ms"], 
            position="J66"
        )

    writer.close()
    print(f"Report Generated with Network and Resource Metrics: {output_file}")

if __name__ == "__main__":
    generate_excel_report()