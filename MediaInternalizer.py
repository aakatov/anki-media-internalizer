import re
import urllib2
import httplib
from aqt.utils import showInfo, showWarning, askUser
from aqt.qt import *
from anki.utils import intTime
from aqt.deckbrowser import DeckBrowser
from HTMLParser import HTMLParser

def myShowOptions(self, did):
    """Monkey patching of DeckBrowser._showOptions."""
    m = QMenu(self.mw)
    a = m.addAction(_("Rename"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._rename(did))
    a = m.addAction(_("Options"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._options(did))
    a = m.addAction(_("Export"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._export(did))
    a = m.addAction(_("Delete"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._delete(did))
    # patch: add the menu item
    a = m.addAction("Internalize Media")
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._internalize(did))
    # patch end
    m.exec_(QCursor.pos())


def retrieveURL(mw, url):
    """Download file into media folder and return local filename or None."""
    req = urllib2.Request(url, None, {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
    resp = urllib2.urlopen(req)
    # ct = resp.info().getheader("content-type")
    filecontents = resp.read()
    # strip off any query string
    url = re.sub(r"\?.*?$", "", url)
    path = unicode(urllib2.unquote(url.encode("utf8")), "utf8")
    return mw.col.media.writeData(path, filecontents)


def internailzeMedia(self, did):
    """Search http-referenced resources in notes, download them into local storage and change the references."""
    if DeckBrowser.internailze_ask_backup and not askUser("Have you backed up your collection and media folder?"):
        return
    DeckBrowser.internailze_ask_backup = False  # don't ask again
    affected_count = 0
    # regex for <img>
    patternImg = re.compile('<img[^>]+(https?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+)[^>]*>', re.IGNORECASE)
    # regex for [sound]
    patternSound = re.compile('\[sound:[^\]]*(https?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+)[^\]]*\]', re.IGNORECASE)
    deck = self.mw.col.decks.get(did)
    nids = self.mw.col.db.list(
        "select distinct notes.id from notes inner join cards on notes.id = cards.nid where cards.did = %d and (lower(notes.flds) like '%%http://%%' or lower(notes.flds) like '%%https://%%')" %
        deck["id"])
    self.mw.progress.start(max=len(nids), min=0, immediate=True)
    try:
        for nid in nids:
            note = self.mw.col.getNote(nid)
            changed = False
            for fld, val in note.items():
                for url in re.findall(patternImg, val) + re.findall(patternSound, val):
                    try:
                        htmlUnescapedUrl = HTMLParser().unescape(url)
                        filename = retrieveURL(self.mw, htmlUnescapedUrl)
                        if filename:
                            val = val.replace(url, filename)
                            changed = True
                    except (IOError, httplib.HTTPException) as e:
                        if not askUser("An error occurred while opening %s\n%s\n\nDo you want to proceed?" % (htmlUnescapedUrl.encode("utf8"), e)):
                            return
            if changed:
                note[fld] = val
                note.flush(intTime())
                affected_count += 1
            self.mw.progress.update()
    finally:
        if affected_count > 0:
            self.mw.col.media.findChanges()
        self.mw.progress.finish()
        showInfo("Deck: %s\nNotes affected: %d" % (deck["name"], affected_count))


DeckBrowser.internailze_ask_backup = True
DeckBrowser._showOptions = myShowOptions
DeckBrowser._internalize = internailzeMedia