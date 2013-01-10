

from Tkinter import *
import tkFileDialog
import tkMessageBox
import dvlr

def callback():
    print "called the callback!"


# Filetype selections for askopenfilename and asksaveasfilename:
PRN_FILE_TYPES=[("space delimited",".prn"),("All files","*")] 

class DvlrGUI:
   def __init__(self):
      self.filenames = None   
      self.save_directory = None
      self.failed_to_process = []     
      self.CreateWidgets()
        
   def CreateWidgets(self):
      self.root=Tk()
      self.root.title("dvlr")
      
      known_formats = []
      for item in dir(dvlr):
         if item.endswith('Writer') and item != 'Writer':
            known_formats.append(getattr(dvlr, item)())

      # Create the menu
      menu = Menu(self.root)
      self.root.config(menu=menu)

      filemenu = Menu(menu, tearoff=False)
      menu.add_cascade(label="File", menu=filemenu)
      filemenu.add_command(label="Quit", command=self.root.quit)

      helpmenu = Menu(menu, tearoff=False)
      menu.add_cascade(label="Help", menu=helpmenu)
      helpmenu.add_command(label="About...", command=self.About)

      self.frame = Frame(self.root, borderwidth=10)
      self.frame.pack()

      self.status_button = Button(  self.frame, 
                                    text    =   "Select files",
                                    command =   self.get_filenames  )
      self.status_button.grid(row=0, column=0, sticky=W)

      self.status_text = Label(self.frame, text="No files selected")
      self.status_text.grid(row=0, column=1, sticky=W)

      self.output_label = Label(self.frame, text="Output as:")
      self.output_label.grid(row=1, column=0, sticky=NW)
      
      self.checkbuttons = []
      
      curr_row = 1
      
      for format in known_formats:
         format_id = format.identifier
         format_label_text = "%s Formatted Files" % format_id
         format_label = Label(self.frame, text=format_label_text)
         format_label.grid(row=curr_row, column=1, sticky=W)
         curr_row += 1
         
         format_options = format.options()
         for option in format_options:
            v = StringVar()
            onval = format_id + ',' + option
            cb = Checkbutton( self.frame, 
                              text      =   option, 
                              variable  =   v, 
                              onvalue   =   onval, 
                              offvalue  =   "")
            cb.var = v
            cb.grid(row=curr_row, column=1, sticky=W)
            self.checkbuttons.append(cb)
            curr_row += 1
            
      
      self.processed_label = Label(self.frame, text="Results:")
      self.processed_label.grid(row=curr_row, column=0, sticky=W)
      self.processed_text = Label(self.frame, text="")
      self.processed_text.grid(row=curr_row, column=1, sticky=W)
      curr_row += 1

      self.run_button = Button( self.frame, 
                                text        =   "Run",
                                command     =   self.process_files,
                                state       =   "disabled"  )
      self.run_button.grid(row=curr_row, columnspan=2)
                
   def get_filenames(self):
      self.filenames=tkFileDialog.askopenfilenames(filetypes=PRN_FILE_TYPES, 
                                            title="Select files to process")
      how_many = len(self.filenames)
      if how_many == 1:
        status_text = "Selected 1 File"
      else:
        status_text = "Selected %d Files" % how_many
      self.status_text.config(text=status_text)
      self.status_text.update_idletasks()
      if self.filenames:
         self.run_button.config(state="active")
         self.run_button.update_idletasks()
         self.run_button.flash()
        
   def process_files(self):
      options = [ cb.var.get() for cb in self.checkbuttons ]
      if not self.filenames:
         return
      (processed, failed) = dvlr.dvlr(self.filenames, options)
      how_many = len(processed)
      if how_many == 1:
         process_text = "Processed 1 file"
      else:
         process_text = "Processed %d files" % how_many
      self.processed_text.config(text=process_text)
      self.processed_text.update_idletasks()
        
   def About(self):
      about_text = """version 0.4.9 
   by Ryan Raaum

Features:
   * works in Windows
   * multiple output formats
   * user-friendly interface
   * python implementation!
      
Past versions:
   * version 0.3, pure perl, David Reddy
   * version 0.2, perl/matlab hybrid, David Reddy
   * version 0.1, ?? """
      tkMessageBox.showinfo("About dvlr...",about_text)
    
   def Run(self):
      self.root.mainloop()

if (__name__=="__main__"):
    DvlrGUI().Run()
