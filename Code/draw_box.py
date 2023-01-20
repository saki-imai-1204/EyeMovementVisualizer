import PIL.Image
from PIL import ImageTk
from tkinter import Frame, Canvas, Button

class DrawBox(Frame):
    def __init__(self, master, image):
        Frame.__init__(self,master=None)
        self.x = self.y = 0
        self.canvas = Canvas(width=1920, height=1080, bg='beige', cursor="cross")
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.rect = None

        self.start_x = None
        self.start_y = None

        #self.im = PIL.Image.open(image)
        self.im = image
        self.wazil,self.lard=self.im.size
        self.canvas.config(scrollregion=(0,0,self.wazil,self.lard))
        self.tk_im = ImageTk.PhotoImage(self.im)
        self.canvas.create_image(0,0,anchor="nw",image=self.tk_im) 

        self.right, self.bottom, self.top, self.left = 0, 0, 0, 0

        def confirm():
            # detecting the left, right, bottom, top of the rectangle
            if self.start_x > self.curX:
                right = self.start_x
                left = self.curX
            else:
                right = self.curX
                left = self.start_x
            if self.start_y > self.curY:
                bottom = self.start_y
                top = self.curY
            else:
                bottom = self.curY
                top = self.start_y
            self.right = right
            self.left = left
            self.top = top
            self.bottom = bottom
            master.destroy()

        # add a confirmation button at the bottom right of the screen
        self.button = Button(self.canvas, text ="Confirm", command = confirm) 
        self.button.place(x = 1850, y = 1000)


    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

        # create rectangle if not yet exist
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, outline='red')

    def on_move_press(self, event):
        curX = self.canvas.canvasx(event.x)
        curY = self.canvas.canvasy(event.y)

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if event.x > 0.9*w:
            self.canvas.xview_scroll(1, 'units') 
        elif event.x < 0.1*w:
            self.canvas.xview_scroll(-1, 'units')
        if event.y > 0.9*h:
            self.canvas.yview_scroll(1, 'units') 
        elif event.y < 0.1*h:
            self.canvas.yview_scroll(-1, 'units')

        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)    

    def on_button_release(self, event):
        # store the x, y coordinates of the rectangle
        self.curX = self.canvas.canvasx(event.x)
        self.curY = self.canvas.canvasy(event.y)
    