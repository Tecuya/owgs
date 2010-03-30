// this is the network client that connects to our real-time server via orbited

Orbited.settings.port = 8001

var NetClient_instance = null;

var NetClient_debug = true;

function NetClient(session_key) { 

    // track our session_key
    this.session_key = session_key;

    // to hold our TCPSocket object
    this.tcp = null;

    // clear to send flag
    this.cts = true;

    // our send queue
    this.sendq = Array();

    // the game_id of the game we are viewing, when applicable
    this.game_id = false;

    this.start = function() { 

        if(NetClient_debug) {
            // TODO .. this breaks eidogo.... odd.. i guess it pisses off DOM enough that eidogo can no longer function....?
            debug_textarea = document.createElement("TEXTAREA");
            debug_textarea.setAttribute("cols", 80);
            debug_textarea.setAttribute("rows", 20);
            debug_textarea.setAttribute("id", "NetClient_debug");

            document.body.appendChild(debug_textarea);

            // innerHTML += "<textarea cols=100 rows=8 id=\"NetClient_debug\"></textarea>";

            this.debug("NetClient.start\n");
        }

        tcp = new LineProtocol(new Orbited.TCPSocket());
        tcp.open('mirrormere.longstair.com',8002,false);

        // theres gotta be a cleaner way to do this!
        tcp.onopen = NetClient_onopen_wrapper;
        tcp.onlinereceived = NetClient_onlinereceived_wrapper;
        tcp.onclose = NetClient_onclose_wrapper;
    }

    this.onlinereceived = function(line) { 
        this.debug("RECV: " + line + "\n");

        dataAr = JSON.parse(line);

        // if there are pending messages, then paste them 
        if(dataAr[0] == "CTS") {
            this.cts = true;
            if(this.sendq.length > 0) { 
                this.send( this.sendq.pop() );
            }

        } else if(dataAr[0] == "JOIN") { 
            part_select = document.getElementById("ParticipantSelect");

            // remove the initial "Loading..." message if it is present
            if(part_select.options[0].value == 0) { 
                part_select.remove(0);
            }
            
            part_select.options.add( new Option(dataAr[2], dataAr[1]) );

            this.updatechat('*** '+dataAr[2]+' has joined the game');

        } else if(dataAr[0] == "PART") { 

            part_select = document.getElementById("ParticipantSelect");
            
            for(var i=0 ; i < part_select.options.length ; i++) { 
                if(part_select.options[i].value == dataAr[1]) { 
                    part_select.remove(i);
                }
            }
            
            this.updatechat('*** '+dataAr[2]+' has left the game');

        } else if(dataAr[0] == "CHAT") {
            this.updatechat('<'+dataAr[1]+'> '+dataAr[2]);
        }
    }

    this.onclose = function(data) { 
        this.debug("NetClient.onclose: " + data + "\n");
    }

    this.send = function(data) { 
        
        // if we aren't clear to send, then just add the message to the send q
        if(this.cts == false) { 
            this.debug("SEND queued: " + data + "\n");
            this.sendq.push(data);
            return;
        }
        
        if (tcp.readyState < 3) {
            this.debug("ERR: Not Connected - ready state " + tcp.readyState + "\n");
        } else if (tcp.readyState > 3 ) {
            this.debug("ERR: Disconnect(ed)(ing)\n");
        } else {
            json_out = JSON.stringify(data);
            this.debug("SEND: " + json_out + "\n");
            this.cts = false;

            // JSON is imported by orbited
            tcp.send(json_out + "\r\n");
        }
    }

    this.connected = function() { 
        this.debug("NetClient.connected\n");
        
        this.send( ["SESS", this.session_key] );
    }

    this.unload = function() { 
        // this doesnt seem to work for whatever reason..
        this.send( ["PART"] );
    }
    
    this.debug = function(msg) { 
        curdate = new Date();
        document.getElementById("NetClient_debug").value += curdate.toLocaleString() + ": " + msg;
    }

    /////////////////////////////////////////
    // higher level commands

    this.joingame = function(game_id) { 
        this.game_id = game_id
        this.sendq.push( ["JOIN", this.game_id] );
    }

    this.chat = function(msg) {
        this.send( ["CHAT", msg] );
    }

    this.updatechat = function(msg) { 
        document.getElementById("ChatTextarea").value += msg + "\r\n";
    }
}


// annoying wrappers for tcpsocket event handlers
function NetClient_onopen_wrapper() { NetClient_instance.connected(); }
function NetClient_onlinereceived_wrapper(data) { NetClient_instance.onlinereceived(data); }
function NetClient_onclose_wrapper(code) { NetClient_instance.onclose(code); }

// init funcs
function NetClient_start() { 
    // window.onunload = NetClient_unload
    // addEventListener("unload", NetClient_unload, false);
    NetClient_instance.start(); 
}
function NetClient_preload(session_key) { NetClient_instance = new NetClient(session_key); }

function NetClient_unload() { 
    NetClient_instance.unload();
}

NetClient_eidogo_player = null


// Load Eidogo
function initEidogo() { 
    var NetClient_eidogo_player = new eidogo.Player({
        container:       "eidogo",
        theme:           "standard",
        // sgfUrl:          "/static/eidogo/sgf/example.sgf",
        sgf:             eidogo_sgf_data,
        sgfPath:         "/static/eidogo/sgf/",
        mode:            "play",
        loadPath:        [0, 0],
        showComments:    true,
        showPlayerInfo:  true,
        showGameInfo:    true,
        showTools:       true,
        showOptions:     true,
        markCurrent:     true,
        markVariations:  true,
        markNext:        false,
        enableShortcuts: false,
        problemMode:     false
    });

    // convenient alias to keep me sane TODO cleanup
    n = NetClient_eidogo_player;
    
    n.createMove('ab');
    n.createMove('de');

}






// This is lifted from orbited's stomp.js STOMP protocol example

// NB: This is loosly based on twisted.protocols.basic.LineReceiver
//     See http://twistedmatrix.com/documents/8.1.0/api/twisted.protocols.basic.LineReceiver.html
// XXX this assumes the lines are UTF-8 encoded.
// XXX this assumes the lines are terminated with a single NL ("\n") character.
LineProtocol = function(transport) {
    // var log = getStompLogger("LineProtocol");
    var self = this;
    var buffer = null;
    var isLineMode = true;

    //
    // Transport callbacks implementation.
    //

    transport.onopen = function() {
        buffer = "";
        isLineMode = true;
        self.onopen();
    };

    transport.onclose = function(code) {
        buffer = null;
        self.onclose(code);
    };

    transport.onerror = function(error) {
        self.onerror(error);
    };

    transport.onread = function(data) {
        // log.debug("transport.onread: enter isLineMode=", isLineMode, " buffer[", buffer.length, "]=", buffer, " data[", data.length, "]=", data);

        if (isLineMode) {
            buffer += data;
            data = "";

            var start = 0;
            var end;
            while ((end = buffer.indexOf("\n", start)) >= 0 && isLineMode) {
                // TODO it would be nice that decode received the
                //      start and end indexes, if it did, we didn't
                //      need the slice copy.
                var bytes = buffer.slice(start, end);
                // TODO do not depend on Orbited.
                var line = Orbited.utf8.decode(bytes)[0];
                // log.debug("fire onlinereceived line[", line.length, "]=", line);
                self.onlinereceived(line);
                start = end + 1;
            }
            // remove the portion (head) of the array we've processed.
            buffer = buffer.slice(start);

            if (isLineMode) {
                // TODO if this buffer length is above a given threshold, we should
                //      send an alert "max line length exceeded" and empty buffer
                //      or even abort.
            } else {
                // we've left the line mode and what remains in buffer is raw data.
                data = buffer;
                buffer = "";
            }
        }

        if (data.length > 0) {
            // log.debug("fire onrawdatareceived data[", data.length, "]=", data);
            self.onrawdatareceived(data);
        }

        // log.debug("transport.onread: leave");
    };

    //
    // Protocol implementation.
    //

    self.setRawMode = function() {
        // log.debug("setRawMode");
        isLineMode = false;
    };

    // TODO although this is a nice interface, it will do a extra copy
    //      of the data, a probable better alternative would be to
    //      make onrawdatareceived return the number of consumed bytes
    //      (instead of making it comsume all the given data).
    self.setLineMode = function(extra) {
        // log.debug("setLineMode: extra=", extra);
        isLineMode = true;
        if (extra && extra.length > 0)
            transport.onread(extra);
    };

    self.send = function(data) {
        // log.debug("send: data=", data);
        return transport.send(data);
    };

    self.open = function(host, port, isBinary) {
        // log.debug("open: host=", host, ':', port, ' isBinary=', isBinary);
        transport.open(host, port, isBinary);
    };

    self.close = function() {
        // log.debug("close");
        transport.close();
    };
    self.reset = function() {
        transport.reset();
    }
    //
    // callbacks for the events generated by this
    //
    // XXX these callbacks names should be camelCased

    self.onopen = function() {};
    self.onclose = function() {};
    self.onerror = function(error) {};
    self.onlinereceived = function(line) {};
    self.onrawdatareceived = function(data) {};
};



