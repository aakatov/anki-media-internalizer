# Overview
Media Internalizer is an addon for [Anki](http://ankisrs.net/). It looks for the notes in a specified deck that have a field containing an HTML tag with http-reference in it, such as `<img src="http://server.com/img.jpg">`. For example, if you use AnkiWeb, it will create external references every time you paste an image.
This addon finds such references, downloads referenced files into Anki's internal local storage and updates the references.
# Installation
1. In Anki, select the Tools > Add-ons > Open Add-ons Folder... menu item.
2. Place the file MediaInternalizer.py in the folder opened.
3. Restart Anki.

# How to Use
Before the use, it's strongly recommended to backup your collection and media folder. See Anki [manual](http://ankisrs.net/docs/manual.html#managing-files-and-your-collection) for the details. 
Make sure that you have Internet connection.

To run the addon, on the main Anki screen, locate the "gears" button to the right of the deck you want to process. Select "Internalize Media" in the drop-down menu.