import customtkinter as ctk
from PIL import Image

#window
window = ctk.CTk()
window.geometry("800x600")
window.columnconfigure(0,weight=2)
window.columnconfigure(1,weight=1)

#label class
class Ezlbl(ctk.CTkLabel):
    pass
#webcam window
frame_1 = ctk.CTkFrame(window, fg_color = "#B3B792")
frame_1.rowconfigure(0,weight=2)
frame_1.grid(row=0,
             column=0,
             columnspan=2,
             rowspan=2,
             padx=10,
             pady=10,
             sticky="nswe")
frame_1.columnconfigure(0,weight=1)
frame_1.columnconfigure(1,weight=1)
frame_1_1 = ctk.CTkFrame(frame_1, fg_color = "#000")
frame_1_1.grid(row=0,
               column=0,
               padx=10,
               pady=10,
               sticky="nswe")
width = frame_1_1.winfo_width() - 50
height = frame_1_1.winfo_height() - 50
ctk_image = ctk.CTkImage(light_image=Image.open("mango.jpg"),size=(300,400))
image_lbl = ctk.CTkLabel(frame_1_1, image=ctk_image,text="mango")
image_lbl.pack(fill="both",expand=True)
frame_1_2 = ctk.CTkFrame(frame_1, fg_color = "transparent")
frame_1_2.grid(row=0,
               column=1,
               padx=10,
               pady=10,
               sticky="nswe")
frame_1_2.columnconfigure(0,weight=1)
frame_1_2.columnconfigure(1,weight=1)
details_lbl = ctk.CTkLabel(frame_1_2, text="Mango Details",
                           text_color="white",
                           anchor="center")
details_lbl.grid(row=0,
                 column=0,
                 columnspan=2,
                 padx=5,
                 pady=5,
                 sticky="nswe")
weight_lbl = ctk.CTkLabel(frame_1_2, text="Weight:",text_color="white")
weight_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
size_lbl = ctk.CTkLabel(frame_1_2, text="Size:",text_color="white")
size_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
ripeness_lbl = ctk.CTkLabel(frame_1_2, text="Ripeness:",text_color="white")
ripeness_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
tss_lbl = ctk.CTkLabel(frame_1_2, text="TSS:",text_color="white")
tss_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
dfct_lbl = ctk.CTkLabel(frame_1_2, text="Defect:",text_color="white")
dfct_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
brs_lbl = ctk.CTkLabel(frame_1_2, text="Bruises:",text_color="white")
brs_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
size_lbl.grid(row=2,column=0,padx=5,pady=5)
size_val.grid(row=2,column=1,padx=5,pady=5)
ripeness_lbl.grid(row=3,column=0,padx=5,pady=5)
ripeness_val.grid(row=3,column=1,padx=5,pady=5)
brs_lbl.grid(row=7,column=0,padx=5,pady=5)
brs_val.grid(row=7,column=1,padx=5,pady=5)

#Counter
grade_lbl = ctk.CTkLabel(frame_1_2, text="Mangoes Graded",text_color="white")
grade_lbl.grid(row=8,column=0,padx=5,pady=5,columnspan=2)
a_lbl = ctk.CTkLabel(frame_1_2, text="Grade A:",text_color="white")
a_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
a_lbl.grid(row=9,column=0,padx=5,pady=5)
a_val.grid(row=9,column=1,padx=5,pady=5)
b_lbl = ctk.CTkLabel(frame_1_2, text="Grade B:",text_color="white")
b_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
b_lbl.grid(row=10,column=0,padx=5,pady=5)
b_val.grid(row=10,column=1,padx=5,pady=5)
c_lbl = ctk.CTkLabel(frame_1_2, text="Grade C:",text_color="white")
c_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
c_lbl.grid(row=11,column=0,padx=5,pady=5)
c_val.grid(row=11,column=1,padx=5,pady=5)
tot_lbl = ctk.CTkLabel(frame_1_2, text="Total:",text_color="white")
tot_val = ctk.CTkLabel(frame_1_2, text="----",text_color="white")
tot_lbl.grid(row=12,column=0,padx=5,pady=5)
tot_val.grid(row=12,column=1,padx=5,pady=5)

#interactable
frame_2 = ctk.CTkFrame(window,fg_color="#B3B792")
frame_2.grid(row=0,
             column=2,
             padx=10,
             pady=10)

##button frame
btn_frame = ctk.CTkFrame(frame_2,fg_color="#000")
btn_frame.grid(row=0,column=0,padx=10,pady=10)
start_btn = ctk.CTkButton(btn_frame,text="start",fg_color="#8AD879")
start_btn.pack()
stop_btn = ctk.CTkButton(btn_frame,text="stop",fg_color="#F3533A")
stop_btn.pack()
exp_btn = ctk.CTkButton(btn_frame,text="export",fg_color="#5CACF9")
exp_btn.pack()

##option frame
opt_frame = ctk.CTkFrame(frame_2,fg_color="#000")
opt_frame.grid(row=1,column=0,padx=10,pady=10)
mng_att_lbl = ctk.CTkLabel(opt_frame,
                           text_color="white",
                           text="Mango Attribute Priority")
mng_att_lbl.grid(column=0,
                 row=0,
                 padx=10,
                 pady=10,
                 stick="nswe")

att_lbl1 = ctk.CTkLabel(opt_frame,
                           text_color="white",
                           text="Sweetness")
optionmenu = ctk.CTkOptionMenu(opt_frame, values=["option 1", "option 2"])
att_lbl2 = ctk.CTkLabel(opt_frame,
                           text_color="white",
                           text="Ripeness")
att_lbl2.grid(column=0,
                 row=3,
                 padx=10,
                 pady=10,
                 stick="nswe")
optionmenu = ctk.CTkOptionMenu(opt_frame, values=["option 1", "option 2"])
optionmenu.grid(column=0,
                row=4,
                padx=10,
                pady=10,
                sticky="nswe")
att_lbl3 = ctk.CTkLabel(opt_frame,
                           text_color="white",
                           text="Size")
att_lbl3.grid(column=0,
                 row=5,
                 padx=10,
                 pady=10,
                 stick="nswe")
optionmenu = ctk.CTkOptionMenu(opt_frame, values=["option 1", "option 2"])
optionmenu.grid(column=0,
                row=6,
                padx=10,
                pady=10,
                sticky="nswe")

att_lbl4 = ctk.CTkLabel(opt_frame,
                           text_color="white",
                           text="Bruising")
att_lbl4.grid(column=0,
                 row=7,
                 padx=10,
                 pady=10,
                 stick="nswe")
optionmenu = ctk.CTkOptionMenu(opt_frame, values=["option 1", "option 2"])
optionmenu.grid(column=0,
                row=8,
                padx=10,
                pady=10,
                sticky="nswe")
#run
window.mainloop()
