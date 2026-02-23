import os
import json
import pandas as pd
import glob
import numpy as np
import re

def get_clean_pod_name(raw_name):
    """Maps ephemeral pod IDs (with hashes) to static group names based on substrings."""
    low_name = raw_name.lower()
    if "large" in low_name: return "large-server-100mb"
    if "medium" in low_name: return "medium-server-10mb"
    if "small" in low_name: return "small-server-1mb"
    if "sidecar" in low_name: return "sidecar"
    if "producer" in low_name: return "producer"
    if "rabbit" in low_name: return "rabbitmq"
    if "siena" in low_name: return "siena"
    if "pst" in low_name: return "pst"
    if "envoy-default" in low_name: return "gateway-envoy"
    return "unknown"

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
                net_data = data.get('network_performance', [])
                
                size_str = str(meta.get('data_size', '0'))
                concurrency = int(meta.get('concurrency', 1))
                success_rate = float(meta.get('success_rate', 1.0))
                
                entry = {
                    "Data Size": size_str,
                    "Concurrency": concurrency,
                    "Success_Rate": success_rate,
                    "Error_Rate": 1.0 - success_rate
                }

                # --- STEP 1: NETWORK LATENCY EXTRACTION ---
                if net_data:
                    net_df = pd.DataFrame(net_data)
                    for metric in ['conn_ms', 'ttfb_ms', 'total_ms']:
                        entry[f"Net_Avg_{metric}"] = net_df[metric].mean()
                        entry[f"Net_P95_{metric}"] = net_df[metric].quantile(0.95)

                # --- STEP 2: POD METRICS EXTRACTION (CLEANED) ---
                for metric_type in ['cpu_usage', 'memory_mb']:
                    results = prom_metrics.get(metric_type, [])
                    for pod_result in results:
                        raw_pod_name = pod_result.get('metric', {}).get('pod', 'unknown')
                        pod_name = get_clean_pod_name(raw_pod_name)
                        all_pods.add(pod_name)

                        values = [float(v[1]) for v in pod_result.get('values', [])]
                        if values:
                            if metric_type == 'cpu_usage':
                                entry[f"CPU_Avg_{pod_name}"] = np.mean(values)
                                entry[f"CPU_P95_{pod_name}"] = np.percentile(values, 95)
                            else:
                                entry[f"Mem_Avg_{pod_name}"] = np.mean(values)
                                entry[f"Mem_P95_{pod_name}"] = np.percentile(values, 95)

                all_summary_data.append(entry)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    # --- STEP 3: GROUPING & AVERAGING ---
    raw_df = pd.DataFrame(all_summary_data)
    df = raw_df.groupby(['Data Size', 'Concurrency'], as_index=False).mean()
    
    # Sort by data size (numeric) then concurrency
    df['Size_Sort'] = df['Data Size'].str.extract(r'(\d+)').astype(int)
    df = df.sort_values(['Size_Sort', 'Concurrency']).drop(columns=['Size_Sort'])

    # --- STEP 4: RATE OF GROWTH CALCULATIONS (SLOPES) ---
    analysis_frames = []
    base_metrics = [c for c in df.columns if any(x in c for x in ["CPU_", "Mem_", "Net_"])]
    
    for size, group in df.groupby('Data Size', sort=False):
        group = group.sort_values('Concurrency')
        for col in base_metrics:
            group[f"Rate_{col}"] = group[col].diff() / group['Concurrency'].diff()
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
            for prefix in series_prefixes:
                # Handle Pod-based metrics (CPU/Mem)
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
                # Handle generic metrics (Latency/Errors)
                else:
                    if prefix in cols:
                        chart.add_series({
                            'name': prefix.replace("Net_", "").replace("Rate_", "Rate "),
                            'categories': ['Summary', start_row, conc_idx, end_row, conc_idx],
                            'values':     ['Summary', start_row, cols.index(prefix), end_row, cols.index(prefix)],
                        })
                        has_data = True

            if has_data:
                chart.set_title({'name': f'{title} ({size})'})
                chart.set_x_axis({'name': 'Concurrency'})
                chart.set_y_axis({'name': y_label})
                ws.insert_chart(position, chart)

        create_chart("Average Memory Usage (e)", "MiB", ["Mem_Avg_"], "B2")
        create_chart("Avg Mem Growth Rate (f)", "MiB/Req", ["Rate_Mem_Avg_"], "J2")
        create_chart("95th Pctl Memory Usage (g)", "MiB", ["Mem_P95_"], "B18")
        create_chart("P95 Mem Growth Rate (h)", "MiB/Req", ["Rate_Mem_P95_"], "J18")

        # --- CPU SECTION ---
        create_chart("Average CPU Usage (a)", "Cores", ["CPU_Avg_"], "B34")
        create_chart("Avg CPU Growth Rate (b)", "Cores/Req", ["Rate_CPU_Avg_"], "J34")
        create_chart("95th Pctl CPU Usage (c)", "Cores", ["CPU_P95_"], "B50")
        create_chart("P95 CPU Growth Rate (d)", "Cores/Req", ["Rate_CPU_P95_"], "J50")

        # --- LATENCY & ERRORS ---
        create_chart("Latency Scaling (i)", "ms", ["Net_Avg_conn_ms", "Net_Avg_ttfb_ms", "Net_Avg_total_ms"], "B66")
        create_chart("Error Rate Scaling (j)", "Rate (0-1)", ["Error_Rate"], "J66")
        
        # Additional useful charts (Rate of Latency Growth)
        create_chart("Total Latency Growth Rate", "ms/Req", ["Rate_Net_Avg_total_ms"], "B82")
    writer.close()
    print(f"Report Generated with full Memory and Scaling analysis: {output_file}")

if __name__ == "__main__":
    generate_excel_report()