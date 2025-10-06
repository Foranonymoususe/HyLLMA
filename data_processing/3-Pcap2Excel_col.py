import os
import pyshark
import pandas as pd


folder_path = r''
tshark_path = r'./tshark.exe'
excel_output_folder = r''

def analyze_pcap(pcap_path, tshark_path):
    cap = pyshark.FileCapture(pcap_path, only_summaries=False, keep_packets=False, tshark_path=tshark_path)
    positives = []
    negatives = []
    intervals = []
    prev_packet_time = None
    site_ip, server_ip = None, None

    try:
        for packet in cap:
            if 'IP' in packet and 'TCP' in packet and int(packet.tcp.len) > 0:
                if site_ip is None or server_ip is None:
                    site_ip = packet.ip.src
                    server_ip = packet.ip.dst

                tcp_payload_size = int(packet.tcp.len)

                if packet.ip.src == site_ip and packet.ip.dst == server_ip:
                    positives.append(tcp_payload_size)
                    negatives.append('')
                else:
                    positives.append('')
                    negatives.append(-tcp_payload_size)

                if prev_packet_time is None:
                    intervals.append(0)
                else:
                    time_interval = float(packet.sniff_timestamp) - prev_packet_time
                    intervals.append(time_interval)

                prev_packet_time = float(packet.sniff_timestamp)
    except Exception as e:
        print(f"{e}")
    finally:
        cap.close()

    all_payloads = [x for x in positives if x != ''] + [abs(x) for x in negatives if x != '']
    if not all_payloads or sum(all_payloads) == 0 or len(all_payloads) < 10:
        return None

    return positives, negatives, intervals


def save_to_excel(positives, negatives, intervals, excel_path):
    max_excel_columns = 16384
    max_data_columns = max_excel_columns - 2

    if len(positives) > max_data_columns:
        positives = positives[:max_data_columns]
        negatives = negatives[:max_data_columns]
        intervals = intervals[:max_data_columns]

    avg_positive = pd.Series([x for x in positives if x != '']).mean()
    avg_negative = pd.Series([x for x in negatives if x != '']).mean()
    avg_interval = pd.Series(intervals).mean()

    data = {
        'Metric': ['Positive_Size_Direction', 'Negative_Size_Direction', 'Interval'],
        'Average': [avg_positive, avg_negative, avg_interval]
    }

    max_length = max(len(positives), len(negatives), len(intervals))
    for index in range(max_length):
        data[index + 1] = [
            positives[index] if index < len(positives) else '',
            negatives[index] if index < len(negatives) else '',
            intervals[index] if index < len(intervals) else ''
        ]

    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)


def process_pcap_files(folder_path, tshark_path, excel_output_folder):
    os.makedirs(excel_output_folder, exist_ok=True)

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.pcap') or file.endswith('.pcapng'):
                pcap_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, folder_path)
                output_folder = os.path.join(excel_output_folder, relative_path)
                os.makedirs(output_folder, exist_ok=True)

                excel_file = os.path.join(output_folder, os.path.basename(pcap_file).rsplit('.', 1)[0] + '.xlsx')

                if os.path.exists(excel_file):
                    print(f"[Skip] {excel_file} already exists, skipping {pcap_file}")
                    continue

                result = analyze_pcap(pcap_file, tshark_path)
                if result is None:
                    print(f"[Skip] {pcap_file} has no valid data (all zeros or less than 10 packets), Excel not generated")
                    continue

                positives, negatives, intervals = result
                save_to_excel(positives, negatives, intervals, excel_file)
                print(f"[Done] Analyzed {pcap_file}, saved to {excel_file}")


if __name__ == "__main__":
    process_pcap_files(folder_path, tshark_path, excel_output_folder)
