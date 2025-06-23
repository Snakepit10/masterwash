import socket
import qrcode
from io import BytesIO
from datetime import datetime

class StampanteTermica:
    """Classe per gestire la stampante termica ESC/POS"""
    
    # Comandi ESC/POS
    ESC = b'\x1b'
    INIT = ESC + b'@'  # Inizializza stampante
    CUT = ESC + b'd\x03'  # Taglia carta
    FEED = b'\n'
    BOLD_ON = ESC + b'E\x01'  # Grassetto ON
    BOLD_OFF = ESC + b'E\x00'  # Grassetto OFF
    ALIGN_LEFT = ESC + b'a\x00'  # Allinea sinistra
    ALIGN_CENTER = ESC + b'a\x01'  # Allinea centro
    ALIGN_RIGHT = ESC + b'a\x02'  # Allinea destra
    FONT_SIZE_NORMAL = ESC + b'!\x00'  # Font normale
    FONT_SIZE_DOUBLE = ESC + b'!\x11'  # Font doppio
    UNDERLINE_ON = ESC + b'-\x01'  # Sottolineato ON
    UNDERLINE_OFF = ESC + b'-\x00'  # Sottolineato OFF
    
    def __init__(self, ip, porta=9100, timeout=5):
        self.ip = ip
        self.porta = porta
        self.timeout = timeout
        self.connesso = False
    
    def connetti(self):
        """Connette alla stampante"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.ip, self.porta))
            self.connesso = True
            return True
        except Exception as e:
            print(f"Errore connessione stampante: {e}")
            self.connesso = False
            return False
    
    def disconnetti(self):
        """Disconnette dalla stampante"""
        if self.connesso:
            try:
                self.socket.close()
            except:
                pass
            self.connesso = False
    
    def invia_comando(self, comando):
        """Invia comando alla stampante"""
        if not self.connesso:
            return False
        
        try:
            if isinstance(comando, str):
                comando = comando.encode('utf-8', errors='ignore')
            self.socket.send(comando)
            return True
        except Exception as e:
            print(f"Errore invio comando: {e}")
            return False
    
    def stampa_testo(self, testo):
        """Stampa testo semplice"""
        if not self.connetti():
            return False
        
        try:
            # Inizializza stampante
            self.invia_comando(self.INIT)
            
            # Invia testo
            self.invia_comando(testo)
            
            # Feed e taglio
            self.invia_comando(self.FEED * 3)
            self.invia_comando(self.CUT)
            
            return True
        except Exception as e:
            print(f"Errore stampa: {e}")
            return False
        finally:
            self.disconnetti()
    
    def stampa_ricevuta(self, testo_ricevuta):
        """Stampa ricevuta formattata"""
        if not self.connetti():
            return False
        
        try:
            # Inizializza
            self.invia_comando(self.INIT)
            self.invia_comando(self.ALIGN_CENTER)
            
            # Header con logo ASCII
            logo_ascii = """
    ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ 
    ████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
    ██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝
    ██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗
    ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║
    ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
    
    ██╗    ██╗ █████╗ ███████╗██╗  ██╗
    ██║    ██║██╔══██╗██╔════╝██║  ██║
    ██║ █╗ ██║███████║███████╗███████║
    ██║███╗██║██╔══██║╚════██║██╔══██║
    ╚███╔███╔╝██║  ██║███████║██║  ██║
     ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    """
            
            # Logo semplificato per stampa termica
            self.invia_comando(self.BOLD_ON)
            self.invia_comando("    MASTERWASH\n")
            self.invia_comando("   AUTOLAVAGGIO\n")
            self.invia_comando(self.BOLD_OFF)
            
            # Corpo ricevuta
            self.invia_comando(self.ALIGN_LEFT)
            self.invia_comando(testo_ricevuta)
            
            # Footer
            self.invia_comando(self.ALIGN_CENTER)
            self.invia_comando("\n" + "="*32 + "\n")
            self.invia_comando("Conservare questa ricevuta\n")
            self.invia_comando("per eventuale assistenza.\n")
            self.invia_comando("\nGrazie per aver scelto\n")
            self.invia_comando(self.BOLD_ON)
            self.invia_comando("MASTERWASH!\n")
            self.invia_comando(self.BOLD_OFF)
            self.invia_comando("="*32 + "\n")
            
            # Feed finale e taglio
            self.invia_comando(self.FEED * 4)
            self.invia_comando(self.CUT)
            
            return True
            
        except Exception as e:
            print(f"Errore stampa ricevuta: {e}")
            return False
        finally:
            self.disconnetti()
    
    def stampa_qr_code(self, testo, dimensione=6):
        """Stampa QR code (se supportato dalla stampante)"""
        try:
            # Comando per QR code ESC/POS
            # Questo è un esempio base, varia per modello di stampante
            qr_cmd = (
                b'\x1d(k\x04\x00\x01A' +  # Funzione QR
                bytes([dimensione]) +      # Dimensione modulo
                b'\x00' +                 # Tipo QR
                bytes([len(testo)]) +     # Lunghezza dati
                b'\x00' +
                testo.encode('utf-8') +   # Dati
                b'\x1d(k\x03\x00\x01Q\x30'  # Stampa QR
            )
            
            return self.invia_comando(qr_cmd)
        except:
            return False

def genera_qr_code(testo, dimensione=(100, 100)):
    """Genera QR code come immagine"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(testo)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converti in bytes per eventuale invio
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    except Exception as e:
        print(f"Errore generazione QR: {e}")
        return None

def genera_ricevuta_html(abbonamento, operatore, larghezza_carta=80):
    """Genera HTML per anteprima ricevuta"""
    
    qr_data = f"MASTERWASH-{abbonamento.codice_nfc}-{abbonamento.cliente.telefono}"
    
    html = f"""
    <div class="ricevuta-container" style="width: {larghezza_carta}mm; font-family: monospace; font-size: 12px; margin: 0 auto; padding: 10px; border: 1px solid #ccc;">
        <div style="text-align: center; font-weight: bold; margin-bottom: 10px;">
            <div style="font-size: 16px;">MASTERWASH</div>
            <div style="font-size: 14px;">AUTOLAVAGGIO</div>
        </div>
        
        <div style="border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 5px 0; margin: 10px 0;">
            <div style="text-align: center; font-weight: bold;">RICEVUTA ABBONAMENTO</div>
        </div>
        
        <div style="margin-bottom: 10px;">
            <strong>Cliente:</strong> {abbonamento.cliente.nome_completo}<br>
            <strong>Telefono:</strong> {abbonamento.cliente.telefono}<br>
            {f'<strong>Email:</strong> {abbonamento.cliente.email}<br>' if abbonamento.cliente.email else ''}
        </div>
        
        <div style="border-top: 1px dashed #000; padding-top: 5px; margin-bottom: 10px;">
            <strong>Targa:</strong> {abbonamento.targa}<br>
            <strong>Tipo:</strong> {abbonamento.tipo_abbonamento.title()}<br>
            <strong>Codice NFC:</strong> {abbonamento.codice_nfc}<br>
        </div>
        
        <div style="margin-bottom: 10px;">
            <strong>Accessi totali:</strong> {abbonamento.accessi_totali}<br>
            <strong>Accessi utilizzati:</strong> {abbonamento.accessi_utilizzati}<br>
            <strong>Accessi rimanenti:</strong> {abbonamento.accessi_rimanenti}<br>
        </div>
        
        <div style="margin-bottom: 10px;">
            <strong>Data inizio:</strong> {abbonamento.data_inizio.strftime('%d/%m/%Y')}<br>
            <strong>Data fine:</strong> {abbonamento.data_fine.strftime('%d/%m/%Y')}<br>
        </div>
        
        <div style="border-top: 1px dashed #000; padding-top: 5px; margin-bottom: 10px;">
            <strong>Prezzo:</strong> € {abbonamento.prezzo:.2f}<br>
            <strong>Stato:</strong> {abbonamento.stato_pagamento.replace('_', ' ').title()}<br>
        </div>
        
        <div style="text-align: center; margin: 15px 0;">
            <div id="qrcode-{abbonamento.id}"></div>
            <small>Codice: {abbonamento.codice_nfc}</small>
        </div>
        
        <div style="border-top: 1px dashed #000; padding-top: 5px; margin-bottom: 10px; font-size: 10px;">
            <strong>Data stampa:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
            <strong>Operatore:</strong> {operatore.nome}<br>
        </div>
        
        <div style="text-align: center; border-top: 1px solid #000; padding-top: 10px; font-size: 10px;">
            <div>Conservare questa ricevuta</div>
            <div>per eventuale assistenza.</div>
            <div style="margin-top: 5px; font-weight: bold;">Grazie per aver scelto</div>
            <div style="font-weight: bold;">MASTERWASH!</div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"></script>
    <script>
        // Genera QR code
        var qr = qrcode(0, 'L');
        qr.addData('{qr_data}');
        qr.make();
        document.getElementById('qrcode-{abbonamento.id}').innerHTML = qr.createImgTag(3, 0);
    </script>
    """
    
    return html

def test_connessione_stampante(ip, porta=9100):
    """Test di connessione alla stampante"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, porta))
        sock.close()
        return result == 0
    except:
        return False