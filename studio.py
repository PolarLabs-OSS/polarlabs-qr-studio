"""PolarLabs QR Studio · Responsive interface for Windows ARM64."""
import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import customtkinter as ctk
from PIL import Image, ImageTk
from qr_engine import logo_image, generate

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PolarLabs.QRStudio.Desktop.1")
    except Exception:
        pass

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DESKTOP = Path.home() / "Desktop"
ASSETS = Path(__file__).resolve().parent
BG="#F4F6FA"
PANEL="#FFFFFF"
BORDER="#E8EBF2"
INK="#28384D"
MUTED="#78899E"
SURFACE="#F6F8FB"
MINT="#A9E8DB"
MINT_HOVER="#8DDACB"
DEEP_MINT="#307B71"
LILAC="#EAE6FD"
LILAC_INK="#7668B5"
PEACH="#FFEADA"
DANGER="#AD695D"

class QRStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PolarLabs QR Studio")
        self.geometry("1090x740+125+75")
        self.minsize(720,560)
        self.configure(fg_color=BG)
        self.logo=None
        self.logo_path=None
        self.logo_thumb=None
        self.icon_photo=None
        self.result=None
        self.qr_photo=None
        self.url=tk.StringVar(value="https://www.polarlabs.it/academy")
        self.mode=tk.StringVar(value="Mosaico fedele")
        self.strength=tk.IntVar(value=100)
        self.remove_bg=tk.BooleanVar(value=False)
        self.status=tk.StringVar(value="Pronto per creare il tuo prossimo QR artistico.")
        self._layout_mode=None
        self._resize_job=None
        self._preview_job=None
        try:
            icon=ASSETS/"PolarLabs-QR.ico"
            if icon.exists():self.iconbitmap(str(icon))
        except Exception:
            pass

        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(1,weight=1)
        self.build_header()
        self.build_content()
        self.build_footer()
        for v in (self.url,self.mode,self.strength,self.remove_bg):
            v.trace_add("write",self._changed)
        self.bind("<Configure>",self._on_root_resize,add="+")
        self.bind("<Control-o>",lambda e:self.browse())
        self.bind("<Control-Return>",lambda e:self.create())
        self.bind("<Control-s>",lambda e:self.save("both") if self.result else None)
        self.after(120,self._apply_layout)

    def font(self,size=12,bold=False):
        return ctk.CTkFont(family="Segoe UI",size=size,
                           weight="bold" if bold else "normal")

    def label(self,parent,text="",color=INK,size=12,bold=False,**kwargs):
        return ctk.CTkLabel(parent,text=text,text_color=color,
                            font=self.font(size,bold),**kwargs)

    def button(self,parent,text,command,height=42):
        return ctk.CTkButton(parent,text=text,command=command,
                             fg_color=SURFACE,hover_color="#EAF0F4",
                             text_color=INK,border_color=BORDER,border_width=1,
                             corner_radius=13,height=height,font=self.font(11,True))

    def separator(self,parent):
        ctk.CTkFrame(parent,fg_color=BORDER,height=1).pack(
            fill="x",pady=(17,0))

    def group_label(self,parent,number,title,subtitle):
        header=ctk.CTkFrame(parent,fg_color="transparent")
        header.pack(fill="x",pady=(17,5))
        ctk.CTkLabel(header,text=number,width=31,height=29,
                     fg_color=LILAC,text_color=LILAC_INK,corner_radius=10,
                     font=self.font(10,True)).pack(side="left")
        self.label(header,title,size=12,bold=True).pack(side="left",padx=(10,0))
        self.label(parent,subtitle,MUTED,11,anchor="w").pack(
            fill="x",pady=(0,8))

    def build_header(self):
        self.header=ctk.CTkFrame(self,fg_color="transparent",height=77)
        self.header.grid(row=0,column=0,sticky="ew",padx=25,pady=(16,10))
        self.header.grid_columnconfigure(1,weight=1)
        icon=ASSETS/"PolarLabs-QR.png"
        if icon.exists():
            im=Image.open(icon).convert("RGBA")
            self.icon_photo=ImageTk.PhotoImage(
                im.resize((114,114),Image.Resampling.LANCZOS),master=self)
            ctk.CTkLabel(self.header,image=self.icon_photo,text="",height=65,width=65
                        ).grid(row=0,column=0,rowspan=2,sticky="w")
        else:
            ctk.CTkLabel(self.header,text="▦",width=60,height=60,
                         fg_color=LILAC,text_color=LILAC_INK,
                         corner_radius=15,font=self.font(28,True)
                         ).grid(row=0,column=0,rowspan=2,sticky="w")

        self.title_label=self.label(self.header,"PolarLabs QR Studio",size=22,bold=True,
                                    anchor="w")
        self.title_label.grid(row=0,column=1,sticky="sw",padx=(14,0))
        self.subtitle_label=self.label(self.header,
                          "Trasforma il tuo logo in un QR code artistico.",
                          MUTED,11,anchor="w")
        self.subtitle_label.grid(row=1,column=1,sticky="nw",padx=(14,0),pady=(0,1))
        self.badge=ctk.CTkLabel(self.header,text="●  Funziona offline",
                               font=self.font(11,True),
                               text_color=DEEP_MINT,
                               fg_color="#E5F7F1",corner_radius=15,
                               width=142,height=32)
        self.badge.grid(row=0,column=2,rowspan=2,sticky="e",padx=(12,0))

    def build_content(self):
        # L'intera area e' scorrevole, non solo la colonna sinistra.
        # In modalita' compatta i pannelli si dispongono verticalmente.
        self.body=ctk.CTkScrollableFrame(self,fg_color="transparent",
                        corner_radius=0,
                        scrollbar_button_color="#D6DFE8",
                        scrollbar_button_hover_color="#B9C8D6")
        self.body.grid(row=1,column=0,sticky="nsew",padx=18,pady=(0,4))
        self.left=ctk.CTkFrame(self.body,fg_color=PANEL,corner_radius=23,
                              border_width=1,border_color=BORDER,width=355)
        self.right=ctk.CTkFrame(self.body,fg_color=PANEL,corner_radius=23,
                               border_width=1,border_color=BORDER)
        self.build_controls()
        self.build_preview()

    def build_controls(self):
        content=ctk.CTkFrame(self.left,fg_color="transparent")
        content.pack(fill="both",expand=True,padx=24,pady=(20,18))
        self.label(content,"Il tuo progetto",size=17,bold=True,anchor="w"
                   ).pack(fill="x")
        self.label(content,"Personalizza i dettagli del QR",MUTED,11,
                   anchor="w").pack(fill="x",pady=(2,4))

        self.group_label(content,"01","Logo","Carica un file PNG o SVG")
        drop=ctk.CTkFrame(content,fg_color=SURFACE,corner_radius=15,
                          border_color=BORDER,border_width=1)
        drop.pack(fill="x")
        drop.grid_columnconfigure(1,weight=1)
        self.logo_box=ctk.CTkLabel(drop,text="✦",width=52,height=52,
                                   fg_color=LILAC,text_color=LILAC_INK,
                                   corner_radius=12,font=self.font(21,True))
        self.logo_box.grid(row=0,column=0,padx=(11,9),pady=12,sticky="w")
        logo_words=ctk.CTkFrame(drop,fg_color="transparent")
        logo_words.grid(row=0,column=1,padx=(0,12),sticky="ew")
        logo_words.grid_columnconfigure(0,weight=1)
        self.logo_name=self.label(logo_words,"Nessun logo caricato",INK,11,True,
                                  anchor="w")
        self.logo_name.grid(row=0,column=0,sticky="ew")
        self.label(logo_words,"PNG oppure SVG",MUTED,10,anchor="w"
                   ).grid(row=1,column=0,sticky="ew",pady=(3,0))
        self.button(content,"+   Seleziona logo",self.browse).pack(
            fill="x",pady=(10,0))

        self.group_label(content,"02","Destinazione","Indirizzo web di destinazione")
        self.url_entry=ctk.CTkEntry(content,textvariable=self.url,
                        fg_color=SURFACE,text_color=INK,border_color=BORDER,
                        corner_radius=13,height=44,border_width=1,
                        font=self.font(11),placeholder_text="https://...")
        self.url_entry.pack(fill="x")

        self.group_label(content,"03","Aspetto","I moduli QR compongono la pixel art")
        self.mode_menu=ctk.CTkOptionMenu(content,variable=self.mode,
                        values=("Mosaico fedele","Mosaico soft",
                                "Colori originali","Monocromatico"),
                        fg_color=SURFACE,button_color="#E7EDF3",
                        button_hover_color="#D7E2EC",text_color=INK,
                        dropdown_fg_color=PANEL,dropdown_text_color=INK,
                        dropdown_hover_color=LILAC,
                        corner_radius=13,height=43,font=self.font(11),
                        dropdown_font=self.font(11))
        self.mode_menu.pack(fill="x")
        slider_head=ctk.CTkFrame(content,fg_color="transparent")
        slider_head.pack(fill="x",pady=(18,5))
        self.intensity_caption=self.label(slider_head,"Fedeltà al logo",INK,11,True)
        self.intensity_caption.pack(side="left")
        self.strength_label=self.label(slider_head,"100%",DEEP_MINT,11,True)
        self.strength_label.pack(side="right")
        self.slider=ctk.CTkSlider(content,from_=0,to=100,
                     number_of_steps=100,height=19,
                     progress_color="#76CDBB",fg_color="#DFEBE8",
                     button_color="#66BFAF",button_hover_color="#54AC9C",
                     button_length=18,command=self._slider)
        self.slider.pack(fill="x",pady=(0,12))
        self.slider.set(100)
        self.remover=ctk.CTkSwitch(content,text="Rimuovi sfondo uniforme",
                        variable=self.remove_bg,font=self.font(11),
                        text_color=INK,fg_color="#DCE3EA",
                        progress_color="#77CCBA",button_color="#FFFFFF",
                        switch_width=40,switch_height=21)
        self.remover.pack(anchor="w",pady=(2,5))
        self.label(content,"Utile con PNG non trasparenti.",MUTED,10,
                   anchor="w").pack(fill="x",pady=(0,4))

        self.separator(content)
        self.label(content,"Scansione verificata prima dell'esportazione.",
                   MUTED,10,anchor="w",wraplength=315).pack(
                       fill="x",pady=(11,2))

    def build_preview(self):
        content=ctk.CTkFrame(self.right,fg_color="transparent")
        content.pack(fill="both",expand=True,padx=22,pady=(19,20))
        head=ctk.CTkFrame(content,fg_color="transparent")
        head.pack(fill="x",pady=(0,12))
        self.label(head,"Anteprima QR",INK,17,True).pack(side="left")
        self.verified_tag=ctk.CTkLabel(head,text="Da generare",
                         fg_color=LILAC,text_color=LILAC_INK,
                         corner_radius=12,height=27,
                         font=self.font(10,True),width=100)
        self.verified_tag.pack(side="right")
        self.preview_frame=ctk.CTkFrame(content,fg_color=SURFACE,
                                         corner_radius=20,
                                         border_color="#EBEEF5",border_width=1,
                                         height=400)
        self.preview_frame.pack(fill="x")
        self.preview_frame.pack_propagate(False)
        self.preview_img=ctk.CTkLabel(self.preview_frame,
                          text="▦\n\nQui apparirà il tuo QR\npersonalizzato",
                          text_color=MUTED,font=self.font(15),justify="center")
        self.preview_img.place(relx=0.5,rely=0.5,anchor="center")
        self.preview_frame.bind("<Configure>",self._on_preview_resize,add="+")

        self.detail=self.label(content,"Correzione errori H  ·  In attesa",
                               MUTED,10,anchor="w",wraplength=450)
        self.detail.pack(fill="x",pady=(11,12))
        actions=ctk.CTkFrame(content,fg_color="transparent")
        actions.pack(fill="x")
        for col in range(3):
            actions.grid_columnconfigure(col,weight=1,uniform="export")
        self.btn_png=self.button(actions,"↓  PNG",lambda:self.save("png"),44)
        self.btn_svg=self.button(actions,"↓  SVG",lambda:self.save("svg"),44)
        self.btn_all=ctk.CTkButton(actions,text="↓  Entrambi",
                            command=lambda:self.save("both"),
                            fg_color=LILAC,hover_color="#DAD3F7",
                            text_color=LILAC_INK,corner_radius=13,
                            height=44,font=self.font(11,True))
        for i,b in enumerate((self.btn_png,self.btn_svg,self.btn_all)):
            b.grid(row=0,column=i,sticky="ew",padx=(0,6) if i<2 else (0,0))
        self.enable_exports(False)

    def build_footer(self):
        foot=ctk.CTkFrame(self,fg_color="transparent")
        foot.grid(row=2,column=0,sticky="ew",padx=27,pady=(6,15))
        foot.grid_columnconfigure(0,weight=1)
        self.status_lbl=ctk.CTkLabel(foot,textvariable=self.status,
                        font=self.font(10),text_color=MUTED,anchor="w",
                        justify="left")
        self.status_lbl.grid(row=0,column=0,sticky="ew")
        self.footer_brand=self.label(foot,"●  PolarLabs",DEEP_MINT,11,True)
        self.footer_brand.grid(row=0,column=1,sticky="e",padx=(12,18))
        self.generate_btn=ctk.CTkButton(foot,text="✦  Genera e verifica QR",
                            command=self.create,height=46,width=220,
                            corner_radius=14,fg_color=MINT,
                            hover_color=MINT_HOVER,text_color="#244741",
                            font=self.font(11,True))
        self.generate_btn.grid(row=0,column=2,sticky="e")

    def _on_root_resize(self,event):
        if event.widget is not self:
            return
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job=self.after(130,self._apply_layout)

    def _apply_layout(self):
        self._resize_job=None
        logical=self.winfo_width()/max(self._get_window_scaling(),0.01)
        new_mode="stack" if logical<940 else "columns"
        if new_mode!=self._layout_mode:
            self.left.grid_forget()
            self.right.grid_forget()
            for col in (0,1):
                self.body.grid_columnconfigure(col,weight=0,minsize=0)
            if new_mode=="columns":
                self.body.grid_columnconfigure(0,weight=0,minsize=655)
                self.body.grid_columnconfigure(1,weight=1,minsize=0)
                self.left.grid(row=0,column=0,sticky="nsew",
                               padx=(5,9),pady=5)
                self.right.grid(row=0,column=1,sticky="new",
                                padx=(9,5),pady=5)
            else:
                self.body.grid_columnconfigure(0,weight=1,minsize=0)
                self.left.grid(row=0,column=0,sticky="ew",
                               padx=5,pady=(5,8))
                self.right.grid(row=1,column=0,sticky="ew",
                                padx=5,pady=(8,5))
            self._layout_mode=new_mode
        window_height=self.winfo_height()/max(self._get_window_scaling(),0.01)
        preview_height=400 if new_mode=="columns" else max(220,min(345,int(window_height*0.42)))
        self.preview_frame.configure(height=preview_height)
        if logical<825:
            self.badge.grid_remove()
            self.subtitle_label.configure(text="Crea QR artistici dai tuoi loghi.")
        else:
            self.badge.grid()
            self.subtitle_label.configure(text="Trasforma il tuo logo in un QR code artistico.")
        if logical<900:
            self.footer_brand.grid_remove()
        else:
            self.footer_brand.grid()
        self.status_lbl.configure(wraplength=int(max(250,(logical-100)*self._get_window_scaling())))
        self.after(120,self._redraw_preview)

    def _on_preview_resize(self,event):
        if self.result is not None:
            if self._preview_job:
                self.after_cancel(self._preview_job)
            self._preview_job=self.after(160,self._redraw_preview)

    def _redraw_preview(self):
        self._preview_job=None
        if self.result is None:
            return
        self.update_idletasks()
        w=self.preview_frame.winfo_width()
        h=self.preview_frame.winfo_height()
        side=min(w-48,h-48,880)
        if side<80:
            return
        preview=self.result["image"].resize((side,side),Image.Resampling.NEAREST)
        new_photo=ImageTk.PhotoImage(preview,master=self)
        self.preview_img.configure(image=new_photo,text="")
        self.qr_photo=new_photo

    def _reveal_preview(self):
        if self._layout_mode!="stack":
            return
        self.update_idletasks()
        canvas=self.body._parent_canvas
        bounds=canvas.bbox("all")
        if bounds:
            canvas.yview_moveto(min(1.0,max(0.0,self.right.winfo_y()/max(1,bounds[3]))))

    def _changed(self,*_):
        if hasattr(self,"intensity_caption"):
            self.intensity_caption.configure(
                text="Fedeltà al logo" if self.mode.get()=="Mosaico fedele" 
                else "Intensità del mosaico"
            )
        self.invalidate()

    def _slider(self,value):
        level=int(round(value))
        self.strength_label.configure(text=f"{level}%")
        if self.strength.get()!=level:
            self.strength.set(level)

    def enable_exports(self,yes):
        for b in (self.btn_png,self.btn_svg,self.btn_all):
            b.configure(state="normal" if yes else "disabled")

    def invalidate(self):
        if self.result is None:
            return
        self.result=None
        # Detach image before releasing PhotoImage, preserving Tcl references.
        self.preview_img.configure(image="",text="▦\n\nParametri modificati\nGenera di nuovo il QR")
        self.qr_photo=None
        self.verified_tag.configure(text="Da aggiornare",fg_color=PEACH,
                                     text_color=DANGER)
        self.detail.configure(text="Correzione errori H  ·  Da aggiornare")
        self.enable_exports(False)
        self.status.set("Impostazioni modificate. Rigenera il QR per esportarlo.")

    def browse(self):
        path=filedialog.askopenfilename(title="Seleziona un logo PNG o SVG",
                  filetypes=[("Loghi PNG e SVG","*.png *.svg"),
                             ("PNG","*.png"),("SVG","*.svg")])
        if not path:
            return
        try:
            im=logo_image(path)
        except Exception as exc:
            messagebox.showerror("Logo non valido",str(exc),parent=self)
            return
        self.invalidate()
        self.logo=im
        self.logo_path=path
        name=Path(path).name
        self.logo_name.configure(text=(name[:28]+"…" if len(name)>28 else name))
        thumbnail=im.copy()
        thumbnail.thumbnail((150,150))
        pic=thumbnail.resize((104,104),Image.Resampling.LANCZOS)
        new_photo=ImageTk.PhotoImage(pic,master=self)
        self.logo_box.configure(image=new_photo,text="")
        self.logo_thumb=new_photo
        self.status.set("Logo caricato. Puoi generare il QR.")

    def create(self):
        if self.logo is None:
            messagebox.showinfo("Manca il logo",
                        "Seleziona un logo PNG o SVG.",parent=self)
            return
        self.generate_btn.configure(state="disabled",text="Verifica in corso…")
        self.status.set("Generazione e verifica di scansione in corso…")
        self.update_idletasks()
        try:
            candidate=generate(self.logo,self.url.get(),self.mode.get(),
                               self.strength.get(),self.remove_bg.get())
            self.result=candidate
            self._redraw_preview()
            self.verified_tag.configure(text="✓  Verificato",fg_color="#E5F7F1",
                                         text_color=DEEP_MINT)
            size_message=(f"  ·  Fedeltà {candidate['strength']}%"
                          if candidate['mode']=="Mosaico fedele" else
                          f"  ·  Intensità {candidate['strength']}%")
            self.detail.configure(text=f"{candidate['modules']} × {candidate['modules']} moduli"
                             f"  ·  3/3 test OK"+size_message)
            self.enable_exports(True)
            if self._layout_mode=="stack":
                self.after(90,self._reveal_preview)
            self.status.set("QR verificato: pronto per esportare in PNG o SVG.")
            if candidate["reduced"]:
                self.status.set("QR verificato; intensità ridotta automaticamente per la lettura.")
        except Exception as exc:
            self.result=None
            self.preview_img.configure(image="",text="Generazione non riuscita")
            self.qr_photo=None
            self.enable_exports(False)
            self.status.set("Errore durante la generazione.")
            messagebox.showerror("Impossibile generare il QR",str(exc),parent=self)
        finally:
            self.generate_btn.configure(state="normal",text="✦   Genera e verifica QR")

    def save(self,which):
        if self.result is None:
            messagebox.showinfo("Nessun QR","Genera prima un QR.",parent=self)
            return
        host=re.sub(r"[^A-Za-z0-9_-]+","-",self.result["url"].split("/")[2]).strip("-")
        stem=f"QR_{host}"[:80]
        folder=filedialog.askdirectory(title="Dove salvare i file?",
                                       initialdir=str(DESKTOP),parent=self)
        if not folder:
            return
        target=Path(folder)
        saved=[]
        try:
            if which in ("png","both"):
                f=target/(stem+".png")
                self.result["image"].save(f,optimize=True,dpi=(300,300))
                saved.append(str(f))
            if which in ("svg","both"):
                f=target/(stem+".svg")
                f.write_text(self.result["svg"],encoding="utf-8")
                saved.append(str(f))
            self.status.set("Esportati: "+", ".join(Path(f).name for f in saved))
            if messagebox.askyesno("Esportazione completata",
                        "File salvati:\n\n"+"\n".join(saved)+"\n\nAprire la cartella?",
                        parent=self):
                os.startfile(folder)
        except Exception as exc:
            messagebox.showerror("Errore esportazione",str(exc),parent=self)

if __name__=="__main__":
    QRStudio().mainloop()
