#!/usr/bin/python

from twisted.internet import gtk2reactor # for gtk-2.0
gtk2reactor.install()

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet import reactor

import gtk


class TcpControl(LineReceiver):

    def connectionMade(self):
        self.factory.connection = self
        self.gui = self.factory.gui
        self.gui.connect_events(self)
        print("connected")
        self.sendLine("CLIP")

    def request_clipno(self):
        self.sendLine("CLIP")

    def lineReceived(self, line):
        print "received:", line
        cmd = line[:4].upper()
        if cmd == "CLIP" or cmd == "JUMP":
            try:
                new_clip = int(line[5:])
                self.gui.update_clip(new_clip)
            except ValueError:
                # no next clip number
                pass

    def fullscreen(self, widget=None):
        self.sendLine("FULL")

    def next(self, widget=None):
        self.sendLine("NEXT")

    def prev(self, widget=None):
        self.sendLine("PREV")

    def jump(self, new_clip):
        self.sendLine("CLIP " + str(int(new_clip)))

    def play(self, widget=None):
        self.sendLine("LOAD")

    def stop(self, widget=None):
        self.sendLine("STOP")


class TcpControlFactory(Factory):
    protocol = TcpControl

    def __init__(self, gui):
        self.gui = gui

    def startedConnecting(self, connector):
        self.gui.set_connected(True)

    def clientConnectionLost(self, connector, reason):
        self.gui.set_connected(False)

    def clientConnectionFailed(self, connector, reason):
        self.gui.set_connected(False)

class RemoteControl(object):
    def __init__(self):
        self.tcp = TcpControlFactory(self)
        self.connected = False

        w = gtk.Window(gtk.WINDOW_TOPLEVEL)
        w.set_border_width(5)
        w.resize(320, 1)

        vbox = gtk.VBox()
        vbox.pack_start(self.make_connection_settings())
        vbox.pack_start(gtk.HSeparator())
        vbox.pack_start(self.make_controls())
        w.add(vbox)
        
        w.connect("delete-event", gtk.main_quit)
        w.connect("key_press_event", self.key_press)
        self.connect_controls()
        w.show_all()

        reactor.run()

    def make_connection_settings(self):
        connection_settings = gtk.HBox()
        connection_settings.set_border_width(5)
        self.entry_target = gtk.Entry()
        self.entry_target.connect("activate", self.connect)
        connection_settings.pack_start(self.entry_target)
        self.btn_connect = gtk.Button("connect")
        self.btn_connect.connect("clicked", self.connect)
        connection_settings.pack_start(self.btn_connect, False)
        return connection_settings

    def make_controls(self):
        controls = gtk.HBox()
        controls.set_border_width(5)
        self.btn_prev = gtk.Button("<<<")
        controls.pack_start(self.btn_prev)
        vbox = gtk.VBox()
        self.btn_stop = gtk.Button("STOP")
        vbox.pack_start(self.btn_stop)
        self.entry_clip = gtk.Entry()
        self.entry_clip.set_max_length(5)
        self.entry_clip.set_alignment(0.5)
        self.entry_clip.set_width_chars(4)
        self.entry_clip.connect("activate", self.play)
        vbox.pack_start(self.entry_clip)
        self.btn_play = gtk.Button("PLAY")
        vbox.pack_start(self.btn_play)
        controls.add(vbox)
        self.btn_next = gtk.Button(">>>")
        controls.pack_start(self.btn_next)
        return controls

    def connect_events(self, connection):
        self.connection = connection

    def connect(self, widget):
        if self.connected:
            self.connector.disconnect()
        else:
            target = self.entry_target.get_text()
            print "connecting to", target
            self.connector = reactor.connectTCP(target, 9001, self.tcp)

    def set_connected(self, connected):
        self.connected = connected
        if self.connected:
            self.btn_connect.set_label("disconnect")
        else:
            self.btn_connect.set_label("connect")

    def prev(self, widget=None):
        self.connection.prev()

    def next(self, widget=None):
        self.connection.next()

    def stop(self, widget=None):
        self.connection.stop()

    def play(self, widget):
        new_clip = int(self.entry_clip.get_text())
        self.connection.jump(new_clip)

    def fullscreen(self, widget=None):
        self.connection.fullscreen()

    def connect_controls(self):
        self.btn_prev.connect("clicked", self.prev)
        self.btn_stop.connect("clicked", self.stop)
        self.btn_play.connect("clicked", self.play)
        self.btn_next.connect("clicked", self.next)

    def update_clip(self, new_clip):
        self.entry_clip.set_text(str(int(new_clip)))

    def key_press(self, widget, event):
        keyval = event.keyval
        try:
            if keyval == 65363:
                # right arrow
                self.next()
            elif keyval == 65361:
                # left arrow
                self.prev()
            elif keyval == 65307:
                # escape
                self.stop()
            elif keyval == 65480:
                # F11
                self.fullscreen()
        except Exception, e:
            print(str(type(e)) + ": " + str(e))


if __name__ == "__main__":
    RemoteControl()

