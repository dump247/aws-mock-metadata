#!/usr/bin/python

import os
from Tkinter import Tk, Label, Button, Entry, ACTIVE

root = Tk()
root.wm_title("Enter MFA Token")

Label(root, text="Token").pack()
entry = Entry(root)
entry.pack(padx=5)


def done():
    print entry.get()
    root.destroy()

b = Button(root, text="OK", default=ACTIVE, command=done)
b.pack(pady=5)

entry.focus_force()
root.bind('<Return>', (lambda e, b=b: b.invoke()))
os.system(('''/usr/bin/osascript -e 'tell app "Finder" to set '''
           '''frontmost of process "Python" to true' '''))
root.mainloop()
