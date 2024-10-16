from flask import Flask, render_template, request, send_file
from fpdf import FPDF
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///relatorios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Relatorio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(500))
    imagem = db.Column(db.String(200))

# Criar o banco de dados dentro de um contexto de aplicativo
with app.app_context():
    db.create_all()

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório Gerado', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        images = request.files.getlist('images')  # Obtendo uma lista de imagens
        descriptions = request.form.getlist('descriptions')  # Obtendo uma lista de descrições

        image_paths = []
        for image in images:
            if image:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image.save(image_path)
                image_paths.append(image_path)

        # Salvar no banco de dados
        for desc, img in zip(descriptions, images):
            desc = desc.strip()  # Remover espaços em branco
            novo_relatorio = Relatorio(descricao=desc, imagem=img.filename)
            db.session.add(novo_relatorio)
        
        db.session.commit()

        # Geração do PDF
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 12)

        for img, desc in zip(images, descriptions):
            # Adiciona a imagem ao PDF
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
            pdf.image(image_path, x=10, w=100)
            
            # Adiciona a descrição abaixo da imagem
            pdf.multi_cell(0, 10, desc.strip())

        pdf_output = 'relatorio.pdf'
        pdf.output(pdf_output)

        return send_file(pdf_output, as_attachment=True)

    return render_template('form.html')

@app.route('/relatorios')
def listar_relatorios():
    relatorios = Relatorio.query.all()
    return render_template('relatorios.html', relatorios=relatorios)

if __name__ == '__main__':
    app.run(debug=True)
