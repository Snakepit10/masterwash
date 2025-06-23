#!/usr/bin/env python3
"""
Script per generare icone PWA per MasterWash
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    """Crea un'icona con il logo MasterWash"""
    
    # Crea immagine con sfondo blu
    img = Image.new('RGB', (size, size), color='#2563eb')
    draw = ImageDraw.Draw(img)
    
    # Calcola dimensioni relative
    margin = size // 8
    text_size = size // 6
    
    try:
        # Prova a usare un font del sistema
        font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", text_size)
        font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", text_size // 2)
    except:
        try:
            # Font Windows
            font_large = ImageFont.truetype("arial.ttf", text_size)
            font_small = ImageFont.truetype("arial.ttf", text_size // 2)
        except:
            # Font di default
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Disegna auto emoji/simbolo
    car_size = size // 3
    car_x = (size - car_size) // 2
    car_y = size // 4
    
    # Simbolo auto stilizzato
    draw.rounded_rectangle(
        [car_x, car_y, car_x + car_size, car_y + car_size // 2],
        radius=car_size // 8,
        fill='white'
    )
    
    # Ruote
    wheel_size = car_size // 6
    wheel_y = car_y + car_size // 2 - wheel_size // 2
    
    # Ruota sinistra
    draw.ellipse(
        [car_x + car_size // 8, wheel_y, car_x + car_size // 8 + wheel_size, wheel_y + wheel_size],
        fill='#1e293b'
    )
    
    # Ruota destra
    draw.ellipse(
        [car_x + car_size - car_size // 8 - wheel_size, wheel_y, 
         car_x + car_size - car_size // 8, wheel_y + wheel_size],
        fill='#1e293b'
    )
    
    # Testo MasterWash
    text_y = car_y + car_size + margin
    
    # "MW" grande
    mw_bbox = draw.textbbox((0, 0), "MW", font=font_large)
    mw_width = mw_bbox[2] - mw_bbox[0]
    mw_x = (size - mw_width) // 2
    draw.text((mw_x, text_y), "MW", fill='white', font=font_large)
    
    # "WASH" piccolo
    wash_bbox = draw.textbbox((0, 0), "WASH", font=font_small)
    wash_width = wash_bbox[2] - wash_bbox[0]
    wash_x = (size - wash_width) // 2
    wash_y = text_y + text_size + margin // 4
    draw.text((wash_x, wash_y), "WASH", fill='white', font=font_small)
    
    # Salva l'immagine
    img.save(filename, 'PNG', optimize=True)
    print(f"✅ Creata icona {filename} ({size}x{size})")

def create_favicon():
    """Crea favicon.ico"""
    
    # Crea favicon 32x32
    create_icon(32, 'static/favicon.png')
    
    # Converti in ICO
    try:
        img = Image.open('static/favicon.png')
        img.save('static/favicon.ico', format='ICO', sizes=[(32, 32)])
        os.remove('static/favicon.png')
        print("✅ Creato favicon.ico")
    except Exception as e:
        print(f"⚠️ Errore creazione favicon: {e}")

def main():
    """Crea tutte le icone necessarie"""
    
    print("🎨 Generazione icone MasterWash...")
    
    # Crea directory static se non esiste
    os.makedirs('static', exist_ok=True)
    
    # Crea icone PWA
    create_icon(192, 'static/icon-192.png')
    create_icon(512, 'static/icon-512.png')
    
    # Crea favicon
    create_favicon()
    
    print("🎉 Icone create con successo!")
    print("\n📱 File generati:")
    print("   - static/icon-192.png (PWA)")
    print("   - static/icon-512.png (PWA)")
    print("   - static/favicon.ico (Browser)")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ PIL (Pillow) non installato")
        print("Installa con: pip install Pillow")
    except Exception as e:
        print(f"❌ Errore: {e}")