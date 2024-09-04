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

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(pix_code)
        qr.make(fit=True)

        qr_img = qr.make_image(fill='black', back_color='white').convert('RGB')

        if logo and logo.filename != '':
            logo = Image.open(logo)
            logo_size = (qr_img.size[0] // 4, qr_img.size[1] // 4)
            logo = logo.resize(logo_size, Image.LANCZOS)



            # Create an image with a transparent square where the logo will be placed
            overlay = Image.new('RGBA', qr_img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            square_size = logo_size[0]
            square_center = (overlay.size[0] // 2, overlay.size[1] // 2)
            draw.rectangle([(square_center[0] - square_size // 2, square_center[1] - square_size // 2),
                            (square_center[0] + square_size // 2, square_center[1] + square_size // 2)],
                           outline=None, fill=(255, 255, 255, 0))

            # Paste the logo into the overlay
            overlay.paste(logo, (square_center[0] - logo_size[0] // 2, square_center[1] - logo_size[1] // 2), logo)

            # Composite the QR code and the overlay
            final_img = Image.alpha_composite(qr_img.convert('RGBA'), overlay)
            final_img = final_img.convert('RGB')
        else:
            final_img = qr_img

        rounded_img = add_rounded_corners(final_img, radius=20)

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
        return send_file(file_path, as_attachment=True, download_name='pix_qr_code.png', mimetype='image/png')
    else:
        return "File not found", 404

def add_square_hole(image, logo_size):
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    square_size = logo_size[0] // 2
    square_center = (image.size[0] // 2, image.size[1] // 2)
    draw.rectangle([(square_center[0] - square_size, square_center[1] - square_size),
                  (square_center[0] + square_size, square_center[1] + square_size)],
                 fill=255)
    mask = ImageOps.fit(mask, image.size, centering=(0.5, 0.5))
    image.paste((255, 255, 255), mask=mask)
    return image

def add_rounded_corners(image, radius):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius, fill=255)
    rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    rounded_image.putalpha(mask)
    return rounded_image

if __name__ == '__main__':
    app.run(debug=True)