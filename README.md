# Overview
Media Internalizer is an addon for [Anki](http://ankisrs.net/). It looks for notes in a specified deck that have a field
containing an HTML `<img>` tag or Anki `[sound]` tag with an http-reference in it, such as `<img src="http://server.com/img.jpg">`
or `[sound:https://server.com/audio.mp3]`. 
For example, when you use AnkiWeb, it creates external references to an image every time you paste an image onto a card. Unlike the desktop version,
only the reference is stored and if you try to use Anki without an Internet connection, the image is not visible.
This addon finds such references, downloads the referenced files into Anki's internal local storage and updates the references.

This addon is [published on AnkiWeb](https://ankiweb.net/shared/info/221033553).

# Installation
1. In Anki, select the Tools > Add-ons > Open Add-ons Folder... menu item.
2. Place the file MediaInternalizer.py in the folder opened.
3. Restart Anki.

# How to Use
Before using the addon, it is strongly recommended that you backup your collection and media folder.
See the Anki [manual](http://ankisrs.net/docs/manual.html#managing-files-and-your-collection) for details.
Make sure that you have an Internet connection.

To run the addon, on the main Anki screen, locate the "gears" button to the right of the deck you want to process.
Select "Internalize Media" in the drop-down menu.