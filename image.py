from flask import send_file

def your_image_generation_function(file):
    # 处理上传的表格文件并生成图像
    # ...

    # 保存生成的图像文件（例如，temp.png）
    image_path = 'test.jpg'

    # 使用 send_file 发送图像给客户端
    return send_file(image_path, mimetype='image/png', as_attachment=True)