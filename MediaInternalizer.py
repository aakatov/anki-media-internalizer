from aqt import mw
from aqt.utils import showInfo, showWarning
from aqt.qt import *

import anki.notes
import re
import urllib2


def retrieveURL(mw, url):
	"Download file into media folder and return local filename or None."
	# fetch it into a temporary folder
	try:
		req = urllib2.Request(url, None, {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
		filecontents = urllib2.urlopen(req).read()
	except urllib2.URLError, e:
		showWarning("An error occurred while opening %s\n %s" % (url, e))
		return
		
	path = unicode(urllib2.unquote(url.encode("utf8")), "utf8")
	return mw.col.media.writeData(path, filecontents)

def internailzeMedia():
	"Search http-referenced resources in notes, download them into local storage and change the references."
	affectedCount = 0
	urlPattern = re.compile('(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)')
	deck = mw.col.decks.current()
	if not deck:
		showInfo("Please, select a deck")
		return
	noteIds = mw.col.db.list("select distinct notes.id from notes inner join cards on notes.id = cards.nid where cards.did = %d and (notes.flds like '%%http://%%' or notes.flds like '%%https://%%')" % deck["id"])
	mw.progress.start(max=len(noteIds), min=0, immediate=True) 
	try:
		n = 0
		for nid in noteIds:
			note = anki.notes.Note(mw.col, id=nid)
			changed = False
			for fld, val in note.items():
				match = urlPattern.search(val)
				if match:
					for url in match.groups():
						filename = retrieveURL(mw, url)
						if filename: 
							val = val.replace(url, filename)
							changed = True
					note[fld] = val
			if changed:
				note.flush()
				affectedCount += 1
			n += 1
			mw.progress.update(value=n)
	finally:
		mw.progress.finish()
		
	showInfo("Deck: %s\nNotes affected: %d" % (deck["name"], affectedCount))
		

action = QAction("Internalize deck's media", mw)
mw.connect(action, SIGNAL("triggered()"), internailzeMedia)
mw.form.menuTools.addAction(action)