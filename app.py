from flask import Flask, render_template, request, redirect, url_for
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from io import BytesIO
import base64
import chardet

app = Flask(__name__)


def generate_plot(data):
    # 将字符串格式的时间戳转换为datetime对象
    timestamps = [str(timestamp) for timestamp in data['上报时间']]
    datetime_objects = [datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") for timestamp in timestamps]
    # 计算相邻时间戳的差值（秒）
    time_deltas = [0]
    for i in range(1, len(datetime_objects)):
        time_deltas.append((datetime_objects[i] - datetime_objects[i - 1]).seconds)

    length = len(datetime_objects)
    x_values = data['上报时间'][0:length]
    # Y轴数据：相邻时间戳的秒级差值
    y_values = []
    y = 0
    flag = 0
    last_date = None
    for i in range(length):
        current_date = datetime_objects[i].date()
        last_date = current_date  # 这个是按天算的。
        if data['报警代码'][i] == 934:
            if (flag == 0):
                y = 0
            y += time_deltas[i]
            flag = 1
        elif data['报警代码'][i] == 935:
            if (flag == 1):
                y = 0
            y -= time_deltas[i]
            flag = 0
        y_values.append(y)

    # 使用孤立森林算法检测异常点
    X = pd.DataFrame({'时间戳': x_values, '差值': y_values})
    model = IsolationForest(contamination=0.02)  # 设置异常值占比
    model.fit(X[['差值']])
    y_pred = model.predict(X[['差值']])
    anomaly_indices = np.where(y_pred == -1)
    anomaly_points = X.iloc[anomaly_indices]

    # 保存异常点数据到 Excel 文件
    output_filename = 'static/异常点数据.xlsx'
    # 创建一个新的 DataFrame 来保存异常点数据
    anomaly_data = pd.DataFrame(columns=['上报时间', '报警代码', '差值'])
    anomaly_data['上报时间'] = anomaly_points['时间戳']
    # 假设报警代码是data中的一列
    anomaly_data['报警代码'] = data['报警代码'].iloc[anomaly_points.index]
    anomaly_data['差值'] = anomaly_points['差值']

    # 将新的 DataFrame 写入 Excel 文件
    anomaly_data.to_excel(output_filename, index=False)

    # 绘制折线图
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.plot(x_values, y_values, color='b', label='价值（秒）')
    plt.scatter(anomaly_points['时间戳'], anomaly_points['差值'], color='r', label='异常点')
    plt.axhline(y=0, color='r', linestyle='--')
    plt.xlabel('时间')
    plt.ylabel('价值（秒）')
    plt.title('X-Y坐标系的折线图')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    # 保存图像到文件
    img_path = 'static/plot.png'
    plt.savefig(img_path, format='png')

    plt.close()
    return url_for('static', filename='plot.png'), url_for('static', filename='异常点数据.xlsx')


def detect_encoding(file_path):
    # 使用 chardet 检测文件编码
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        # 保存上传的文件到临时文件
        temp_file_path = 'temp_file.csv'
        file.save(temp_file_path)

        # 检测文件编码并读取文件
        encoding = detect_encoding(temp_file_path)
        df = pd.read_excel(temp_file_path)

        # 生成图像
        plot_data, anomaly_data_download_link = generate_plot(df)

        return render_template('result.html', plot_data=plot_data, anomaly_data_download_link=anomaly_data_download_link)

if __name__ == '__main__':
    app.run(debug=True)
