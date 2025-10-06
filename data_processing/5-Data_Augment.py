import pandas as pd
import numpy as np
import os

def augment_excel_with_detail_logs(input_path: str, output_path: str, mtu: int):
    df = pd.read_excel(input_path)
    df_out = df.copy()

    pos_idx = df_out.index[df_out['Metric'] == 'Positive_Size_Direction'][0]
    neg_idx = df_out.index[df_out['Metric'] == 'Negative_Size_Direction'][0]
    interval_idx = df_out.index[df_out['Metric'].str.contains('interval', case=False)][0]
    cols = df_out.columns[2:]
    n = len(cols)

    pos_arr = df_out.loc[pos_idx, cols].astype(float).to_numpy()
    neg_arr = df_out.loc[neg_idx, cols].astype(float).to_numpy()
    interval_arr = df_out.loc[interval_idx, cols].astype(float).to_numpy()

    changes = []

    def apply_disturbance(arr, metric_name):
        for i in range(n):
            old = arr[i]
            if np.isnan(old) or abs(old) >= mtu:
                continue
            if np.random.rand() < 0.10:
                while True:
                    d = np.random.randint(-100, 101)
                    new = old + d
                    if np.sign(new) == np.sign(old) and abs(new) <= mtu:
                        arr[i] = new
                        changes.append({
                            'type': 'disturb',
                            'metric': metric_name,
                            'col': cols[i],
                            'idx': i,
                            'old': old,
                            'new': new,
                        })
                        break
        return arr

    pos_arr = apply_disturbance(pos_arr, 'Positive_Size_Direction')
    neg_arr = apply_disturbance(neg_arr, 'Negative_Size_Direction')

    def apply_merge(arr, times, metric_name):
        i = 0
        while i < n - 1:
            a, b = arr[i], arr[i + 1]
            if (not np.isnan(a) and not np.isnan(b)
                and abs(a) < mtu and abs(b) < mtu
                and np.sign(a) == np.sign(b)
                and np.random.rand() < 0.15):

                new_size = a + b
                if abs(new_size) <= mtu:
                    new_time = times[i] + times[i + 1]
                    changes.append({
                        'type': 'merge',
                        'metric': metric_name,
                        'idx1': i,
                        'idx2': i + 1,
                        'col1': cols[i],
                        'col2': cols[i + 1],
                        'old1': a,
                        'old2': b,
                        'new_size': new_size,
                        'old_time1': times[i],
                        'old_time2': times[i + 1],
                        'new_time': new_time,
                    })
                    arr[i] = new_size
                    times[i] = new_time
                    arr[i + 1] = np.nan
                    times[i + 1] = np.nan
                    i += 1
                    continue
            i += 1
        return arr, times

    pos_arr, interval_arr = apply_merge(pos_arr, interval_arr, 'Positive_Size_Direction')
    neg_arr, interval_arr = apply_merge(neg_arr, interval_arr, 'Negative_Size_Direction')

    def apply_retransmit_both(pos_arr, neg_arr, times):
        for i in range(1, n):
            pos_v = pos_arr[i]
            neg_v = neg_arr[i]
            if np.isnan(pos_v) and np.isnan(neg_v):
                continue
            if np.random.rand() < 0.15:
                step = np.random.randint(1, 6)
                j = i + step
                if j < n:
                    temp_pos = pos_v
                    temp_neg = neg_v
                    temp_time = times[i]

                    for t in range(i, j):
                        pos_arr[t] = pos_arr[t + 1]
                        neg_arr[t] = neg_arr[t + 1]
                        times[t] = times[t + 1]

                    pos_arr[j] = temp_pos
                    neg_arr[j] = temp_neg
                    times[j] = temp_time

                    metric = 'Positive_Size_Direction' if not np.isnan(pos_v) else 'Negative_Size_Direction'
                    changes.append({
                        'type': 'retransmit',
                        'metric': metric,
                        'from_idx': i,
                        'to_idx': j,
                        'from_col': cols[i],
                        'to_col': cols[j],
                        'value': temp_pos if metric == 'Positive_Size_Direction' else temp_neg,
                        'time': temp_time,
                    })
        return pos_arr, neg_arr, times

    def apply_time_retransmit(pos_arr, neg_arr, times):
        for i in range(1, n):
            if np.isnan(times[i]):
                continue
            if np.random.rand() < 0.24:
                step = np.random.randint(1, 6)
                j = i + step
                if j < n:
                    temp_pos = pos_arr[i]
                    temp_neg = neg_arr[i]
                    temp_time = times[i]
                    for t in range(i, j):
                        pos_arr[t] = pos_arr[t + 1]
                        neg_arr[t] = neg_arr[t + 1]
                        times[t] = times[t + 1]
                    pos_arr[j] = temp_pos
                    neg_arr[j] = temp_neg
                    times[j] = temp_time
                    print(f"[Time Retransmit] {cols[i]} → {cols[j]} : time={temp_time:.3f}")
        return pos_arr, neg_arr, times

    pos_arr, neg_arr, interval_arr = apply_retransmit_both(pos_arr, neg_arr, interval_arr)
    pos_arr, neg_arr, interval_arr = apply_time_retransmit(pos_arr, neg_arr, interval_arr)

    for i in range(1, n):
        old_t = interval_arr[i]
        if np.isnan(old_t):
            continue
        if np.random.rand() < 0.6:
            d = np.random.uniform(0.001, 0.1)
            new_t = old_t + d
            interval_arr[i] = new_t
            print(f"[Time Disturbance] Column {cols[i]} : {old_t:.3f} → {new_t:.3f}")

    df_out.loc[pos_idx, cols] = pos_arr
    df_out.loc[neg_idx, cols] = neg_arr
    df_out.loc[interval_idx, cols] = interval_arr
    df_out.to_excel(output_path, index=False)

    for c in changes:
        if c['type'] == 'disturb':
            print(f"[Disturb] {c['metric']} @ {c['col']} : {c['old']:.1f} → {c['new']:.1f}")
        elif c['type'] == 'merge':
            print(f"[Merge] {c['metric']} @ {c['col1']}+{c['col2']} : "
                  f"size {c['old1']:.1f}+{c['old2']:.1f}→{c['new_size']:.1f}, "
                  f"time {c['old_time1']:.3f}+{c['old_time2']:.3f}→{c['new_time']:.3f}")
        elif c['type'] == 'retransmit':
            print(f"[Retransmit] {c['metric']} from {c['from_col']} to {c['to_col']} : "
                  f"value={c['value']:.1f}, time={c['time']:.3f}")

if __name__ == '__main__':
    input_path = ''
    mtu = 1428
    output_dir = ''
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0] + '_augmented.xlsx'

    for i in range(1, 1700):
        numbered_name = f"{i}-{base_name}"
        output_path = os.path.join(output_dir, numbered_name)
        print(f"[{i:03d}] Generating augmented file: {output_path}")
        augment_excel_with_detail_logs(
            input_path=input_path,
            output_path=output_path,
            mtu=mtu
        )
