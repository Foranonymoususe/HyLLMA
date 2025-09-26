import pandas as pd
import numpy as np
import os

def augment_excel_with_detail_logs(input_path: str, output_path: str, mtu: int):
    # 读取并复制表格
    df = pd.read_excel(input_path)
    df_out = df.copy()

    # 特征行定位行与列
    pos_idx = df_out.index[df_out['Metric']=='Positive_Size_Direction'][0]
    neg_idx = df_out.index[df_out['Metric']=='Negative_Size_Direction'][0]
    interval_idx = df_out.index[df_out['Metric'].str.contains('interval', case=False)][0]
    cols = df_out.columns[2:]
    n = len(cols)

    # 提取三条序列为 numpy 数组
    pos_arr = df_out.loc[pos_idx,cols].astype(float).to_numpy()
    neg_arr = df_out.loc[neg_idx,cols].astype(float).to_numpy()
    interval_arr = df_out.loc[interval_idx, cols].astype(float).to_numpy()

    changes = []  # 变动记录

    # 1-扰动，对小于MTU的报文正负大小随机扰动，扰动范围-100～100
    # 报文大小扰动概率设置为0.1
    def apply_disturbance(arr, metric_name):
        for i in range(n):
            old = arr[i]
            if np.isnan(old) or abs(old) >= mtu:
                continue
            if np.random.rand() < 0.1:  # 概率1-报文扰动（设置为0.1）
                # 生成[-100,100]内的随机扰动 d
                # 只保留新旧同符号且不超过 MTU 的情况
                while True:
                    d = np.random.randint(-100, 101)
                    new = old + d
                    if np.sign(new) == np.sign(old) and abs(new) <= mtu:
                        arr[i] = new
                        changes.append({
                            'type':'disturb',
                            'metric':metric_name,
                            'col':cols[i],
                            'idx':i,
                            'old':old,
                            'new':new,
                        })
                        break
        return arr

    pos_arr = apply_disturbance(pos_arr, 'Positive_Size_Direction')
    neg_arr = apply_disturbance(neg_arr, 'Negative_Size_Direction')

    # 2) 合并
    # 报文合并概率设置为0.15
    def apply_merge(arr, times, metric_name):
        i = 0
        while i < n - 1:
            a, b = arr[i], arr[i+1]
            if (not np.isnan(a) and not np.isnan(b)
                and abs(a) < mtu and abs(b) < mtu
                and np.sign(a) == np.sign(b)
                and np.random.rand() < 0.15):  # 概率2:报文大小合并概率（设置为0.15）

                new_size = a + b
                if abs(new_size) <= mtu:
                    new_time = times[i] + times[i+1]
                    # 把原索引、列名、旧值和新值存到 changes 列表，打印日志
                    changes.append({
                        'type':      'merge',
                        'metric':    metric_name,
                        'idx1':      i,
                        'idx2':      i+1,
                        'col1':      cols[i],
                        'col2':      cols[i+1],
                        'old1':      a,
                        'old2':      b,
                        'new_size':  new_size,
                        'old_time1': times[i],
                        'old_time2': times[i+1],
                        'new_time':  new_time,
                    })
                    arr[i]   = new_size
                    times[i] = new_time
                    arr[i+1]   = np.nan
                    times[i+1] = np.nan
                    
                    i += 1
                    continue
            i += 1
        return arr, times

    pos_arr, interval_arr = apply_merge(pos_arr, interval_arr, 'Positive_Size_Direction')
    neg_arr, interval_arr = apply_merge(neg_arr, interval_arr, 'Negative_Size_Direction')

    # 3) 重传
    # 报文重传概率设置为0.15
    def apply_retransmit_both(pos_arr, neg_arr, times):
        for i in range(1,n):
        # 1) 判断当前位置是正向包还是负向包
            pos_v = pos_arr[i]
            neg_v = neg_arr[i]
        # 如果两种方向都没有包，跳过
            if np.isnan(pos_v) and np.isnan(neg_v):
                continue

        # 2) 触发重传
            if np.random.rand() < 0.15:  # 概率3-报文重传概率（设置为0.15）
                step = np.random.randint(1, 6)
                j = i + step
                if j < n:
                # 3) 先把当前位置的数据（三个数组的一行）缓存下来
                    temp_pos  = pos_v
                    temp_neg  = neg_v
                    temp_time = times[i]

                # 4) “删除” i 位置：把 i+1 ... n-1 全部左移 1 格
                    for t in range(i,j):
                        pos_arr[t] = pos_arr[t+1]
                        neg_arr[t] = neg_arr[t+1]
                        times[t]   = times[t+1]

                # 5) 把缓存的数据放到 j 上
                    pos_arr[j]  = temp_pos
                    neg_arr[j]  = temp_neg
                    times[j]    = temp_time

                # 6) 记录这次重传
                    metric = 'Positive_Size_Direction' if not np.isnan(pos_v) else 'Negative_Size_Direction'
                    changes.append({
                        'type':      'retransmit',
                        'metric':    metric,
                        'from_idx':  i,
                        'to_idx':    j,
                        'from_col':  cols[i],
                        'to_col':    cols[j],
                        'value':     temp_pos if metric=='Positive_Size_Direction' else temp_neg,
                        'time':      temp_time,
                    })

        return pos_arr, neg_arr, times

    # 4）时间重传
    # 时间重传概率设置为0.24
    def apply_time_retransmit(pos_arr, neg_arr, times):
        for i in range(1,n):
            # 只有当该位置有间隔值才考虑
            if np.isnan(times[i]):
                continue
            if np.random.rand() < 0.24:  # 概率4-时间重传（设置为0.24）
                step = np.random.randint(1, 6)
                j = i + step
                if j < n:
                    # 缓存原来的三组数据
                    temp_pos  = pos_arr[i]
                    temp_neg  = neg_arr[i]
                    temp_time = times[i]
                    # 向前“删除” i 位置：把 i+1 ... j 依次左移 1 格
                    for t in range(i, j):
                        pos_arr[t] = pos_arr[t+1]
                        neg_arr[t] = neg_arr[t+1]
                        times[t]   = times[t+1]
                    # 在 j 位置“插入”缓存的数据
                    pos_arr[j]  = temp_pos
                    neg_arr[j]  = temp_neg
                    times[j]    = temp_time
                    # 打印重传日志
                    print(f"[时间重传] 从 {cols[i]} → {cols[j]} : "
                          f"time={temp_time:.3f}")
        return pos_arr, neg_arr, times

    # 报文大小重传调用
    pos_arr, neg_arr, interval_arr = apply_retransmit_both(
        pos_arr, neg_arr, interval_arr
    )
    # 时间重传调用
    pos_arr, neg_arr, interval_arr = apply_time_retransmit(
        pos_arr, neg_arr, interval_arr
    )

    # 5）对于已经增强的数据进行时间扰动
    # 时间扰动概率设置为0.6
    for i in range(1,n):
        old_t = interval_arr[i]
        if np.isnan(old_t):
            continue
        # 触发时间扰动
        if np.random.rand() < 0.6:  # 概率5-时间扰动概率（设置为0.6）
            d = np.random.uniform(0.001, 0.1)
            new_t = old_t + d
            interval_arr[i] = new_t
            # 直接打印到控制台
            print(f"[时间扰动] 列 {cols[i]} : {old_t:.3f} → {new_t:.3f}")
            
    # 写回并保存
    df_out.loc[pos_idx,      cols] = pos_arr
    df_out.loc[neg_idx,      cols] = neg_arr
    df_out.loc[interval_idx, cols] = interval_arr
    df_out.to_excel(output_path, index=False)


    # 打印变动详情
    print("=== 变动详情 ===")
    for c in changes:
        if c['type']=='disturb':
            print(f"[扰动] {c['metric']} @ {c['col']} : "
                  f"{c['old']:.1f} → {c['new']:.1f}")
        elif c['type']=='merge':
            print(f"[合并] {c['metric']} @ {c['col1']}+{c['col2']} "
                  f": size {c['old1']:.1f}+{c['old2']:.1f}→{c['new_size']:.1f}, "
                  f"time {c['old_time1']:.3f}+{c['old_time2']:.3f}→{c['new_time']:.3f}")
        elif c['type']=='retransmit':
            print(f"[重传] {c['metric']} 从 {c['from_col']}  "
                  f"到 {c['to_col']} : value={c['value']:.1f}, "
                  f"time={c['time']:.3f}")


if __name__ == '__main__':
    # 原始输入文件
    input_path  = '/Users/hetianyi/Desktop/flightsim/flightsim_excel/scan/flightsim_c2_run15_20250925_202746_flow_2_17.171.47.23_192.168.1.6_288pkts.xlsx'
    mtu         = 1428

    # 固定的输出目录
    output_dir = '/Users/hetianyi/Desktop/flightsim/flightsim_augment/scan'
    os.makedirs(output_dir, exist_ok=True)

    # 构造文件名称
    base_name = os.path.splitext(os.path.basename(input_path))[0] + '_augmented.xlsx'

    # 循环生成多个增强文件
    for i in range(1, 1700):
        numbered_name = f"{i}-{base_name}"
        output_path   = os.path.join(output_dir, numbered_name)
        print(f"[{i:03d}] 生成增强文件：{output_path}")
        augment_excel_with_detail_logs(
            input_path  = input_path,
            output_path = output_path,
            mtu  = mtu
        )
