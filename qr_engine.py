"""PolarLabs QR Studio - motore QR a pixel con verifica tramite ZXing."""
from io import BytesIO
import colorsys
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape
from PIL import Image, ImageDraw, ImageOps
import qrcode
import zxingcpp
import resvg_py

BG_DARK=(22,38,50)
BG_LIGHT=(255,255,255)
WOLF_DARK=(68,124,143)
WOLF_LIGHT=(181,215,228)
WAVE_DARK=(13,141,133)
WAVE_LIGHT=(173,234,223)

def mix(a,b,t):
    return tuple(int(round(a[i]*(1-t)+b[i]*t)) for i in range(3))

def logo_image(path):
    path=Path(path)
    if not path.is_file(): raise ValueError("Seleziona un logo PNG o SVG esistente.")
    if path.suffix.lower()==".svg":
        raw=resvg_py.svg_to_bytes(svg_path=str(path),width=1000,height=1000)
        im=Image.open(BytesIO(raw)).convert("RGBA")
    elif path.suffix.lower()==".png":
        im=Image.open(path).convert("RGBA")
    else: raise ValueError("Sono supportati solo PNG e SVG.")
    if max(im.size)>4000:
        im.thumbnail((4000,4000),Image.Resampling.LANCZOS)
    return im

def square_logo(im, remove_bg=False):
    im=im.convert("RGBA")
    if remove_bg:
        p=im.load()
        corners=[p[0,0],p[im.width-1,0],p[0,im.height-1],p[im.width-1,im.height-1]]
        # Usa il colore dell'angolo solo se gli angoli sono simili.
        if max(sum(abs(c[i]-corners[0][i]) for i in range(3)) for c in corners)<48:
            base=corners[0]
            out=im.copy()
            pix=out.load()
            for y in range(out.height):
                for x in range(out.width):
                    c=pix[x,y]
                    diff=max(abs(c[i]-base[i]) for i in range(3))
                    if diff<38:pix[x,y]=(c[0],c[1],c[2],0)
            im=out
    box=Image.new("RGBA",(1000,1000),(0,0,0,0))
    im.thumbnail((1000,1000),Image.Resampling.LANCZOS)
    box.alpha_composite(im,((1000-im.width)//2,(1000-im.height)//2))
    return box

def verify_url(url):
    url=url.strip()
    parsed=urlparse(url)
    if parsed.scheme.lower() not in ("http","https") or not parsed.netloc:
        raise ValueError("Inserisci un URL completo, ad esempio https://www.polarlabs.it/academy")
    if len(url.encode("utf8"))>350:raise ValueError("URL troppo lungo: massimo 350 byte.")
    return url

def tint(color, dark, mode):
    """Palette vivide sui moduli scuri e pastello sui moduli chiari.

    Ogni bit resta scuro/chiaro in modo da preservare il contrasto
    necessario al lettore QR. Il logo emerge da entrambe le classi di bit.
    """
    r,g,b=color[:3]
    if mode=="PolarLabs":
        wave_ratio=min(1.0,max(0.0,(float(g)-107.0)/49.0))
        return mix(WOLF_DARK if dark else WOLF_LIGHT,
                   WAVE_DARK if dark else WAVE_LIGHT,wave_ratio)
    if mode=="Monocromatico":
        return (72,123,136) if dark else (183,218,228)
    # Mantieni la tinta cromatica del logo, limitandone luminosita' e
    # saturazione separatamente per bit scuri e chiari.
    hue,saturation,value=colorsys.rgb_to_hsv(r/255.0,g/255.0,b/255.0)
    if saturation<0.12:
        hue,saturation=0.52,0.45
    if dark:
        saturation=max(0.40,min(0.70,saturation*0.78))
        value=0.53+0.04*value
    else:
        saturation=max(0.14,min(0.30,saturation*0.32))
        value=0.90+0.02*value
    return tuple(int(round(v*255)) for v in colorsys.hsv_to_rgb(
        hue,saturation,value))

def render(logo,url,mode="PolarLabs",intensity=100,size=1590,remove_bg=False):
    url=verify_url(url)
    if mode not in ("PolarLabs","Colori originali","Monocromatico"):
        mode="PolarLabs"
    intensity=max(0,min(100,int(intensity)))
    qr=qrcode.QRCode(version=7,error_correction=qrcode.constants.ERROR_CORRECT_H,box_size=1,border=0)
    qr.add_data(url)
    qr.make(fit=True)
    matrix=qr.get_matrix()
    n=len(matrix)
    if n>137:raise ValueError("URL troppo lungo per un QR artistico leggibile.")
    source=square_logo(logo,remove_bg).resize((n,n),Image.Resampling.LANCZOS)
    px=source.load()
    colors=[]
    for y in range(n):
        rr=[]
        for x in range(n):
            isdark=bool(matrix[y][x])
            base=BG_DARK if isdark else BG_LIGHT
            r,g,b,a=px[x,y]
            alpha=((a/255.0)**0.72)*(intensity/100.0)
            art=tint((r,g,b),isdark,mode)
            c=mix(base,art,alpha)
            if (x<9 and y<9) or (x>=n-8 and y<9) or (x<9 and y>=n-8):
                c=base
            rr.append(c)
        colors.append(rr)
    quiet=4
    side=n+quiet*2
    raw=Image.new("RGB",(side,side),BG_LIGHT)
    draw=ImageDraw.Draw(raw)
    for y,row in enumerate(colors):
        for x,color in enumerate(row):draw.point((x+quiet,y+quiet),fill=color)
    raster=raw.resize((size,size),Image.Resampling.NEAREST)
    return raster,colors,quiet,url

def svg_from(colors,quiet,url):
    n=len(colors);side=n+quiet*2
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1590" height="1590" viewBox="0 0 {side} {side}" shape-rendering="crispEdges" role="img" aria-label="QR artistico">',
           f'<title>{escape(url)}</title>',
           f'<rect width="{side}" height="{side}" fill="#ffffff"/>']
    for y,row in enumerate(colors):
        x=0
        while x<n:
            rgb=row[x];stop=x+1
            while stop<n and row[stop]==rgb:stop+=1
            code="#%02x%02x%02x"%rgb
            lines.append(f'<rect x="{x+quiet}" y="{y+quiet}" width="{stop-x}" height="1" fill="{code}"/>')
            x=stop
    lines.append("</svg>")
    return "\n".join(lines)

def decode_test(image,url):
    status=[]
    for side in (800,450,280):
        reduced=image.resize((side,side),Image.Resampling.BOX)
        b=zxingcpp.read_barcode(reduced,formats=zxingcpp.BarcodeFormat.QRCode)
        status.append(bool(b and b.text==url))
    return status

def generate(logo,url,mode="Mosaico fedele",intensity=100,remove_bg=False):
    url=verify_url(url)
    if mode=="Mosaico fedele":
        from pixel_mosaic import render_mosaic
        return render_mosaic(logo,url,mode,intensity,remove_bg,square_logo,
                             svg_from,decode_test)
    if mode in ("Mosaico soft","PolarLabs (mosaico)"):
        mode="PolarLabs"
    # Riduce l'intensita' solo se il lettore non conferma la scansione.
    values=[intensity]+[intensity*x//100 for x in (85,70,55,40,25,0)]
    seen=set()
    for strength in values:
        if strength in seen:continue
        seen.add(strength)
        image,colors,quiet,url=render(logo,url,mode,strength,1590,remove_bg)
        tests=decode_test(image,url)
        if all(tests):
            return {"image":image,"svg":svg_from(colors,quiet,url),
                    "url":url,"mode":mode,"strength":strength,"tests":tests,
                    "modules":len(colors),"reduced":strength<intensity}
    raise ValueError("Non e' stato possibile verificare la scansione del QR.")

def create_icon(path):
    im=Image.new("RGBA",(128,128),(12,23,37,255))
    d=ImageDraw.Draw(im)
    aqua=(86,222,207,255)
    white=(234,255,252,255)
    for x,y in ((16,16),(84,16),(16,84)):
        d.rectangle((x,y,x+28,y+28),fill=white)
        d.rectangle((x+6,y+6,x+22,y+22),fill=(12,23,37,255))
        d.rectangle((x+10,y+10,x+18,y+18),fill=aqua)
    d.rectangle((54,62,72,80),fill=aqua)
    d.rectangle((87,87,105,105),fill=aqua)
    d.rectangle((54,90,70,106),fill=white)
    im.save(path,sizes=[(16,16),(32,32),(48,48),(64,64),(128,128)])
