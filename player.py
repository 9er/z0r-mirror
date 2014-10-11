#!/usr/bin/env python2

from twisted.internet import gtk2reactor # for gtk-2.0
gtk2reactor.install()

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet import reactor

import gtk
import webkit

from os import path


class TcpControl(LineReceiver):

    def connectionMade(self):
        self.controls = self.factory.controls # self.factory isn't available in __init__
        print("tcp client has connected")
        self.controls.connect_new_clip(self.clip_loaded)

    def connectionLost(self, reason):
        self.controls.disconnect_new_clip(self.clip_loaded)

    def request_clipno(self):
        self.sendLine("CLIP")

    def lineReceived(self, line):
        cmd = line[:4].upper()
        if cmd == "CLIP" or cmd == "JUMP":
            try:
                new_clip = int(line[5:])
                self.controls.jump(new_clip)
            except ValueError:
                # no next clip number --> return active clip no
                self.sendLine("CLIP " + str(self.controls.clip))
        elif cmd == "NEXT":
            self.controls.next()
        elif cmd == "PREV":
            self.controls.prev()
        elif cmd == "LOAD":
            self.controls.load()
        elif cmd == "FULL":
            self.controls.toggle_fullscreen()
        elif cmd == "STOP":
            self.controls.stop()
        elif cmd == "QUIT":
            self.controls.quit()

    def clip_loaded(self, new_clip):
       self.sendLine("CLIP " + str(self.controls.clip)) 


class TcpControlFactory(Factory):
    protocol = TcpControl
    def __init__(self, controls):
        self.controls = controls


class FullscreenToggler(object):
    """ from: http://stackoverflow.com/questions/5234434/simple-way-to-toggle-fullscreen-with-f11-in-pygtk """
    def __init__(self, window, keysym=gtk.keysyms.F11):
        self.window = window
        self.keysym = keysym
        self.window_is_fullscreen = False
        self.window.connect_object('window-state-event', FullscreenToggler.on_window_state_change, self)
        self.window.connect_object("key_press_event", FullscreenToggler.key_press, self)

    def on_window_state_change(self, event):
        self.window_is_fullscreen = bool(
            gtk.gdk.WINDOW_STATE_FULLSCREEN & event.new_window_state)

    def toggle(self):
        if self.window_is_fullscreen:
            self.window.unfullscreen()
        else:
            self.window.fullscreen()

    def key_press(self, event):
        if event.keyval == self.keysym:
            self.toggle()


class Controls(object):
    def __init__(self, window, view, fs_toggler):
        self.clip = 0
        self.view = view
        self.fs_toggler = fs_toggler
        window.connect_object("key_press_event", Controls.key_press, self)
        self.callbacks_new_clip = []
        self.load()

    def connect_new_clip(self, callback):
        self.callbacks_new_clip.append(callback)

    def disconnect_new_clip(self, callback):
        self.callbacks_new_clip.remove(callback)

    def toggle_fullscreen(self):
        self.fs_toggler.toggle()

    def load(self):
        uri = path.join(path.dirname(path.abspath(__file__)), "swf-files/" + str(self.clip) + ".swf")
        self.view.open(uri)
        print "loading clip " + str(self.clip) + " from " + uri + " (http://www.z0r.de/" + str(self.clip) + ")"
        for callback in self.callbacks_new_clip:
            callback(self.clip)

    def jump(self, new_clip):
        self.clip = new_clip
        self.load()

    def stop(self):
        self.view.open("")

    def prev(self):
        self.clip -= 1
        self.load()

    def next(self):
        self.clip += 1
        self.load()

    def key_press(self, event):
        keyval = event.keyval
        if keyval == 65363:
            # right arrow
            self.next()
        elif keyval == 65361:
            # left arrow
            self.prev()
        elif keyval == 65307:
            # escape
            self.stop()
        elif keyval == 32:
            # space
            self.next()

    def quit(self):
        gtk.main_quit()


class Player(object):
    def __init__(self):
        w = gtk.Window(gtk.WINDOW_TOPLEVEL)
        w.resize(800,600)
        
        view = webkit.WebView()
        sw = gtk.ScrolledWindow()
        sw.add(view)
        w.add(sw)
        w.show_all()

        w.connect("delete-event", gtk.main_quit)

        fs_toggler = FullscreenToggler(w)
        controls = Controls(w, view, fs_toggler)
        reactor.listenTCP(9001, TcpControlFactory(controls))
        reactor.run()


if __name__ == "__main__":
    player = Player()

