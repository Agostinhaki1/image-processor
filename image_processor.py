from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont
import os
import io
import base64
import requests
from datetime import datetime

app = Flask(__name__)

# Configurações
FONTS_DIR = './fonts'
ASSETS_DIR = './assets'
OUTPUT_DIR = './output'
TEMP_DIR = './temp'

# Criar diretórios se não existirem
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Fontes
FONTS = {
    'montserrat_bold': os.path.join(FONTS_DIR, 'Montserrat-Bold.ttf'),
    'montserrat_black': os.path.join(FONTS_DIR, 'Montserrat-Black.ttf'),
    'inter_regular': os.path.join(FONTS_DIR, 'Inter-Regular.ttf'),
    'inter_medium': os.path.join(FONTS_DIR, 'Inter-Medium.ttf')
}

def get_font(nome, tamanho):
    """Carrega fonte ou usa padrão"""
    try:
        fonte_map = {
            'Montserrat': FONTS['montserrat_bold'],
            'Inter': FONTS['inter_regular']
        }
        caminho = fonte_map.get(nome, FONTS['inter_regular'])
        size = int(tamanho.replace('px', ''))
        return ImageFont.truetype(caminho, size)
    except Exception as e:
        print(f"Erro ao carregar fonte {nome}: {e}")
        return ImageFont.load_default()

def hex_to_rgb(hex_color):
    """Converte hex para RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_text_with_wrap(draw, text, font, max_width, x, y, fill, line_height=1.4):
    """Desenha texto com quebra automática"""
    words = text.split(' ')
    lines = []
    current_line = ''
    
    for word in words:
        test_line = current_line + word + ' '
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + ' '
    
    if current_line:
        lines.append(current_line.strip())
    
    current_y = y
    font_height = font.size
    
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += int(font_height * line_height)
    
    return current_y

@app.route('/', methods=['GET'])
def home():
    """Página inicial"""
    return jsonify({
        'service': 'Image Processor API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'process': '/process-slide (POST)',
            'download': '/download/<filename> (GET)'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'image-processor',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/process-slide', methods=['POST'])
def process_slide():
    """Processa um slide"""
    try:
        data = request.json
        print(f"📥 Recebendo requisição: {data.get('id', 'sem-id')}")
        
        # 1. BAIXAR IMAGEM DALL-E
        dalle_url = data.get('imagem_dalle_path') or data.get('dalle_image_url')
        print(f"🖼️  Baixando imagem: {dalle_url}")
        
        if dalle_url.startswith('http'):
            response = requests.get(dalle_url, timeout=30)
            img = Image.open(io.BytesIO(response.content))
        else:
            img = Image.open(dalle_url)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # 2. PROCESSAR CAMADA DE TEXTO
        camada_texto = data.get('camada_texto', {})
        
        # TÍTULO
        if 'titulo' in camada_texto:
            print("✍️  Renderizando título...")
            titulo = camada_texto['titulo']
            font = get_font(titulo['fonte'], titulo['tamanho'])
            color = hex_to_rgb(titulo['cor'])
            
            texto = titulo.get('quebra_linha') or titulo['texto']
            linhas = texto.split('\n')
            
            y_pos = titulo['posicao']['y']
            line_height = int(titulo['tamanho'].replace('px', '')) * 1.2
            
            for linha in linhas:
                draw.text((titulo['posicao']['x'], y_pos), linha, font=font, fill=color)
                y_pos += line_height
        
        # LINHA DECORATIVA
        if 'elementos_graficos' in camada_texto:
            print("🎨 Adicionando elementos gráficos...")
            for elemento in camada_texto['elementos_graficos']:
                if elemento['tipo'] == 'linha_decorativa':
                    pos = elemento['posicao'].replace('px', '').split(', ')
                    x, y = int(pos[0]), int(pos[1])
                    largura = int(elemento['tamanho'].replace('px', ''))
                    cor = hex_to_rgb(elemento['cor'])
                    espessura = int(elemento['espessura'].replace('px', ''))
                    draw.line([(x, y), (x + largura, y)], fill=cor, width=espessura)
                
                elif elemento['tipo'] == 'badge':
                    width = img.size[0]
                    cor_bg = hex_to_rgb(elemento['background'])
                    draw.rectangle([(width-120, 40), (width-40, 80)], fill=cor_bg)
                    badge_font = get_font('Inter', '18px')
                    draw.text((width-100, 55), elemento['texto'], font=badge_font, fill=(255, 255, 255))
        
        # SUBTÍTULO
        if 'subtitulo' in camada_texto:
            print("✍️  Renderizando subtítulo...")
            sub = camada_texto['subtitulo']
            font = get_font(sub['fonte'], sub['tamanho'])
            color = hex_to_rgb(sub['cor'])
            max_width = sub.get('largura_maxima', img.size[0] - 160)
            draw_text_with_wrap(draw, sub['texto'], font, max_width, sub['posicao']['x'], sub['posicao']['y'], color)
        
        # DESCRIÇÃO
        if 'descricao' in camada_texto:
            print("📝 Renderizando descrição...")
            desc = camada_texto['descricao']
            font = get_font(desc['fonte'], desc['tamanho'])
            color = hex_to_rgb(desc['cor'])
            max_width = desc.get('largura_maxima', img.size[0] - 160)
            line_height = desc.get('linha_altura', 1.6)
            draw_text_with_wrap(draw, desc['texto'], font, max_width, desc['posicao']['x'], desc['posicao']['y'], color, line_height)
        
        # BULLET POINTS
        if 'bullet_points' in camada_texto:
            print("🔵 Renderizando bullet points...")
            y_offset = camada_texto.get('descricao', {}).get('posicao', {}).get('y', 500) + 120
            x_start = camada_texto.get('subtitulo', {}).get('posicao', {}).get('x', 80)
            
            for bullet in camada_texto['bullet_points']:
                font = get_font('Inter', '22px')
                color = hex_to_rgb('#0066FF' if bullet.get('destaque') else '#666666')
                draw.text((x_start, y_offset), bullet['icone'], font=font, fill=color)
                draw.text((x_start + 30, y_offset), bullet['texto'], font=font, fill=color)
                y_offset += 40
        
        # LOGO
        camada_marca = data.get('camada_marca', {})
        if 'logo' in camada_marca:
            print("🎯 Adicionando logo...")
            try:
                logo_path = os.path.join(ASSETS_DIR, 'logo.png')
                if os.path.exists(logo_path):
                    logo = Image.open(logo_path)
                    logo_size = camada_marca['logo'].get('tamanho', 80)
                    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                    
                    if logo.mode != 'RGBA':
                        logo = logo.convert('RGBA')
                    
                    logo_x = 80
                    logo_y = img.size[1] - logo_size - 80
                    
                    if 'right' in camada_marca['logo'].get('posicao', ''):
                        logo_x = img.size[0] - logo_size - 80
                    
                    img.paste(logo, (logo_x, logo_y), logo)
            except Exception as e:
                print(f"⚠️  Erro ao carregar logo: {e}")
        
        # HANDLE
        if 'handle' in camada_marca:
            print("📱 Adicionando handle...")
            handle = camada_marca['handle']
            font = get_font('Inter', handle['tamanho'])
            color = hex_to_rgb(handle['cor'])
            
            handle_x = img.size[0] - 80
            handle_y = img.size[1] - 60
            
            bbox = draw.textbbox((0, 0), handle['texto'], font=font)
            text_width = bbox[2] - bbox[0]
            
            if 'right' in handle.get('posicao', ''):
                handle_x -= text_width
            
            draw.text((handle_x, handle_y), handle['texto'], font=font, fill=color)
        
        # 3. SALVAR
        slide_id = data.get('id', f"slide_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        output_filename = f"{slide_id}_final.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        print(f"💾 Salvando: {output_path}")
        img.save(output_path, 'PNG', quality=90, optimize=True)
        
        file_size = os.path.getsize(output_path)
        file_size_kb = file_size / 1024
        
        print(f"✅ Processamento concluído! {file_size_kb:.2f}KB")
        
        return jsonify({
            'status': 'sucesso',
            'slide_id': slide_id,
            'arquivo': output_filename,
            'caminho_completo': output_path,
            'tamanho_arquivo': f"{file_size_kb:.2f}KB",
            'dimensoes': f"{img.size[0]}x{img.size[1]}",
            'formato': 'PNG',
            'timestamp': datetime.now().isoformat(),
            'download_url': f'/download/{output_filename}'
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERRO: {error_trace}")
        return jsonify({
            'status': 'erro',
            'erro': str(e),
            'stack': error_trace,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Baixar arquivo"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/png')
    return jsonify({'erro': 'Arquivo não encontrado'}), 404

if __name__ == '__main__':
    print("🚀 Image Processor Service INICIADO!")
    print("📍 Porta: 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
```

#### **4. `.dockerignore`**
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.git/
.gitignore
README.md
.DS_Store
