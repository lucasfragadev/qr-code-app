from flask import Flask, render_template, request, send_file
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps
import qrcode
from io import BytesIO
import base64
import uuid

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    qr_code_filename = None
    if request.method == 'POST':
        pix_code = request.form['pix_code']
        logo = request.files['logo']
        fill_color = request.form.get('fill_color', 'black')
        back_color = request.form.get('back_color', 'white')

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(pix_code)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')

        if logo and logo.filename != '':
            logo = Image.open(logo).convert("RGBA")
            logo_size = (qr_img.size[0] // 4, qr_img.size[1] // 4)
            logo = logo.resize(logo_size, Image.LANCZOS)

            mask = Image.new('L', qr_img.size, 255)
            draw = ImageDraw.Draw(mask)
            square_size = logo_size[0]
            square_center = (mask.size[0] // 2, mask.size[1] // 2)
            draw.rectangle([(square_center[0] - square_size // 2, square_center[1] - square_size // 2),
                            (square_center[0] + square_size // 2, square_center[1] + square_size // 2)],
                           fill=0)

            qr_img = Image.composite(qr_img, Image.new('RGBA', qr_img.size, 'white'), mask)

            logo_position = (square_center[0] - logo_size[0] // 2, square_center[1] - logo_size[1] // 2)
            qr_img.paste(logo, logo_position, logo)

        rounded_img = add_rounded_corners(qr_img, radius=20)

        img_io = BytesIO()
        rounded_img.save(img_io, 'PNG')
        img_io.seek(0)

        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex
        qr_code_filename = f"qr_code_{timestamp}_{unique_id}.png"

        static_dir = 'static'
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)

        rounded_img.save(os.path.join(static_dir, qr_code_filename), 'PNG')

        return render_template('index.html', img_data=img_base64, qr_code_filename=qr_code_filename)

    return render_template('index.html', img_data=None)

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join('static', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name='qr_code.png', mimetype='image/png')
    else:
        return "File not found", 404

def add_rounded_corners(image, radius):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius, fill=255)
    rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    rounded_image.putalpha(mask)
    return rounded_image

if __name__ == '__main__':
    app.run(debug=True)
