"""PolarLabs QR Studio: mosaico autentico, costruito esclusivamente da moduli QR.

Ogni tassello mantiene la funzione scuro/chiaro del QR. Nessun logo
sovrapposto, nessuna immagine inserita nel codice esportato.
"""
from PIL import Image,ImageDraw
import qrcode
import colorsys

BG_DARK=(97,109,118)
BG_WHITE=(255,255,255)
FUNCTION_DARK=(19,35,46)

def blend(a,b,amount):
    return tuple(int(round(a[i]*(1-amount)+b[i]*amount)) for i in range(3))

def perceived(rgb):
    return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]

def module_palette(color,dark):
    """Conserva il colore del logo in due luminosita' scanner-safe."""
    r,g,b=color
    # Per i loghi troppo chiari, ricaviamo un tono visibile senza
    # ridisegnarne la forma (luminanza piu' bassa, tinta conservata).
    h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if s<0.08 and v>.82:
        r,g,b=180,190,195
    if dark:
        lum=perceived((r,g,b))
        factor=min(.92,94/max(lum,1))
        return tuple(max(13,int(c*factor)) for c in (r,g,b))
    out=blend((r,g,b),(255,255,255),.47)
    if perceived(out)<166:
        out=blend(out,(255,255,255),.20)
    return out

def protected(x,y,n):
    # I tre marcatori e relative zone di separazione restano intatti.
    return ((x<9 and y<9) or (x>=n-9 and y<9) or
            (x<9 and y>=n-9) or x==6 or y==6)

def artwork_for_matrix(logo,n,fidelity,remove_bg,square_logo):
    logo=square_logo(logo,remove_bg).convert("RGBA")
    fraction=.64+.18*(fidelity/100.0)
    art_size=max(12,int(round(n*fraction)))
    src=logo.resize((art_size,art_size),Image.Resampling.LANCZOS)
    square=Image.new("RGBA",(n,n),(0,0,0,0))
    square.alpha_composite(src,((n-art_size)//2,(n-art_size)//2))
    return square

def draw_colors(matrix,artwork,fidelity):
    n=len(matrix)
    data=artwork.load()
    colors=[]
    background_strength=fidelity/100
    outside=blend((28,45,56),BG_DARK,background_strength)
    for y in range(n):
        row=[]
        for x in range(n):
            dark=bool(matrix[y][x])
            r,g,b,alpha=data[x,y]
            if protected(x,y,n):
                out=FUNCTION_DARK if dark else BG_WHITE
            elif alpha<50:
                out=outside if dark else BG_WHITE
            else:
                rgb=module_palette((r,g,b),dark)
                # Pixel pieno anche sui bordi del disegno. Per aree
                # antialias, aumenta la copertura senza usare trasparenza.
                if alpha<105:
                    t=(alpha-50)/55
                    out=blend(outside if dark else BG_WHITE,rgb,t)
                else:
                    out=rgb
            row.append(out)
        colors.append(row)
    return colors

def render_mosaic(logo,url,mode,intensity,remove_bg,square_logo,
                  svg_from,decode_test):
    fidelity=max(0,min(100,int(intensity)))
    # Maggiore matrice = piu' tessere per disegnare fedelmente il logo.
    # Non accorcia e non altera mai l'URL dell'utente.
    sizes=(12,11,10,9,8,7)
    for version in sizes:
        qr=qrcode.QRCode(version=version,box_size=1,border=0,
                         error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(url)
        try:
            qr.make(fit=True)
        except Exception:
            continue
        matrix=qr.get_matrix()
        n=len(matrix)
        if n>137:
            continue
        artwork=artwork_for_matrix(logo,n,fidelity,remove_bg,square_logo)
        # Moduli tutti intatti: solo colore/luminanza vengono modificati.
        colors=draw_colors(matrix,artwork,fidelity)
        raw=Image.new("RGB",(n+8,n+8),BG_WHITE)
        draw=ImageDraw.Draw(raw)
        for y,row in enumerate(colors):
            for x,col in enumerate(row):
                draw.point((x+4,y+4),fill=col)
        png=raw.resize((1590,1590),Image.Resampling.NEAREST)
        tests=decode_test(png,url)
        if all(tests):
            return {
                "image":png,
                "svg":svg_from(colors,4,url),
                "url":url,
                "mode":"Mosaico fedele",
                "strength":fidelity,
                "tests":tests,
                "modules":n,
                "reduced":False
            }
    # A volte un logo molto carico richiede un pattern QR piu' scuro.
    # In tale caso riduciamo il contrasto artistico, mai i bit codificati.
    for fidelity2 in (75,50,25,0):
        qr=qrcode.QRCode(version=12,box_size=1,border=0,
                         error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(url);qr.make(fit=True)
        matrix=qr.get_matrix();n=len(matrix)
        artwork=artwork_for_matrix(logo,n,min(fidelity,fidelity2),
                                    remove_bg,square_logo)
        colors=draw_colors(matrix,artwork,min(fidelity,fidelity2))
        raw=Image.new("RGB",(n+8,n+8),BG_WHITE)
        d=ImageDraw.Draw(raw)
        for y,row in enumerate(colors):
            for x,col in enumerate(row): d.point((x+4,y+4),fill=col)
        png=raw.resize((1590,1590),Image.Resampling.NEAREST)
        tests=decode_test(png,url)
        if all(tests):
            return {"image":png,"svg":svg_from(colors,4,url),"url":url,
                    "mode":"Mosaico fedele","strength":min(fidelity,fidelity2),
                    "tests":tests,"modules":n,"reduced":True}
    raise ValueError("Questo logo e URL non hanno superato la verifica del QR.")
