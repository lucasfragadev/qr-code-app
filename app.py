from flask import Flask, render_template, request, send_file
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    qr_code_image = None  # Para armazenar a imagem do QR code
    if request.method == 'POST':
        # Carregar dados do formulário
        pix_code = request.form['pix_code']
        logo = request.files['logo']
        
        # Gerar QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(pix_code)
        qr.make(fit=True)

        # Criar imagem do QR Code
        img = qr.make_image(fill='black', back_color='white').convert('RGB')

        # Verifica se um logo foi enviado e o processa
        if logo and logo.filename != '':
            logo = Image.open(logo)
            logo_size = (img.size[0] // 4, img.size[1] // 4)
            logo = logo.resize(logo_size, Image.LANCZOS)
            logo_position = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
            img.paste(logo, logo_position, logo)

        # Adicionar bordas arredondadas
        rounded_img = add_rounded_corners(img, radius=20)
        
        # Salvar a imagem em um buffer de memória
        img_io = BytesIO()
        rounded_img.save(img_io, 'PNG')
        img_io.seek(0)

        # Converter a imagem para base64 para exibição no HTML
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        # Preparar a imagem para download
        qr_code_image = img_io.getvalue()
        
        # Renderizar a página com a imagem e a opção de download
        return render_template('index.html', img_data=img_base64)
    
    return render_template('index.html', img_data=None)

@app.route('/download')
def download():
    # Criar um buffer de memória para o download
    img_io = BytesIO()
    img_io.write(request.args['img_data'].encode('utf-8'))
    img_io.seek(0)
    
    return send_file(img_io, as_attachment=True, download_name='pix_qr_code.png', mimetype='image/png')

def add_rounded_corners(image, radius):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius, fill=255)
    rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    rounded_image.putalpha(mask)
    return rounded_image

if __name__ == '__main__':
    app.run(debug=True)
