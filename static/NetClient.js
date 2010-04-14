// this is the network client that connects to our real-time server via orbited

Orbited.settings.port = 8001

var NetClient_instance = null;

var NetClient_debug = true;

function NetClient(session_key) { 

    // track our session_key
    this.session_key = session_key;

    // to hold our TCPSocket object
    this.tcp = null;

    // to hold our LineReceiver object
    this.line = null;

    // clear to send flag
    this.cts = true;

    // our send queue
    this.sendq = Array();

    // the game_id of the game we are viewing, when applicable
    this.game_id = false;

    this.start = function() { 

        if(NetClient_debug) {
            debug_textarea = document.createElement("TEXTAREA");
            debug_textarea.setAttribute("cols", 80);
            debug_textarea.setAttribute("rows", 20);
            debug_textarea.setAttribute("id", "NetClient_debug");

            document.body.appendChild(debug_textarea);

            this.debug("NetClient.start\n");
        }

        this.tcp = new Orbited.TCPSocket();
        this.line = new LineProtocol(this.tcp);
        this.line.open('mirrormere.longstair.com',8002,false);

        // theres gotta be a cleaner way to do this!
        this.line.onopen = NetClient_onopen_wrapper;
        this.line.onlinereceived = NetClient_onlinereceived_wrapper;
        this.line.onclose = NetClient_onclose_wrapper;
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

            if(part_select.options[0].value == 0) { 
                part_select.remove(0);
            }
            
            part_select.options.add( new Option(dataAr[2] + ' ('+dataAr[3]+')', dataAr[1]) );

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

        } else if(dataAr[0] == "MOVE") { 

            NetClient_eidogo_player.createMove(dataAr[1], true);

        } else if(dataAr[0] == "OFFR") { 

            this.receivedoffer(dataAr[1], dataAr[2], dataAr[3], dataAr[4], dataAr[5], dataAr[6]);

        } else if(dataAr[0] == "BEGN") { 

            window.location.reload();

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
        

        if (this.tcp.readyState < 3) {
            this.debug("ERR: Not Connected - ready state " + this.tcp.readyState + "\n");
        } else if (this.tcp.readyState > 3 ) {
            this.debug("ERR: Disconnect(ed)(ing)\n");
        } else {
            json_out = JSON.stringify(data);
            this.debug("SEND: " + json_out + "\n");
            this.cts = false;

            // JSON is imported by orbited
            this.tcp.send(json_out + "\r\n");
        }
    }

    this.connected = function() { 
        this.debug("NetClient.connected\n");
        
        this.send( ["SESS", this.session_key] );
    }

    this.unload = function() { 
        // reset our tcpsocket when we unload so the server can notify others that we left
        this.tcp.reset();
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

    this.chat = function(chatinput) {
        this.send( ["CHAT", chatinput.value] );
        chatinput.value = '';
    }

    this.updatechat = function(msg) { 
        if(ta = document.getElementById("ChatTextarea"))
            ta.value += msg + "\r\n";

        
        if(NetClient_eidogo_player != null) 
            NetClient_eidogo_player.dom.comments.innerHTML += msg.replace('<','&lt;').replace('>','&gt;') + "<br>";
            
    }

    this.onmove = function(data) { 
        coord = data[0];
        color = data[1];

        // TODO support getting the parent node from eidogo to enable variations!
        parent_node = 0;
        
        // TODO support getting a copy of all the comments made since the last move from eidogo
        comments = "";

        this.send( ["MOVE", coord, color, parent_node, comments] )
    }

    // this func is called when the game owner decides he's ready to start the game
    this.startgame = function(data) { 
        parts = document.getElementById('ParticipantSelect');
        selected_user = parts.options[ parts.selectedIndex ].value;

        this.send( ["BEGN", selected_user ] )
    }

    // this func is called when challenders click the "Offer to Play" button
    this.makeoffer = function() { 
        board_size = document.getElementById("offer_BoardSize").value;
        main_time = document.getElementById("offer_MainTime").value;
        komi = document.getElementById("offer_Komi").value;
        my_color = document.getElementById("offer_Color").value;
        
        this.send( ["OFFR", board_size, main_time, komi, my_color] )
    }

    // this func is called when an offer is received
    this.receivedoffer = function(board_size, main_time, komi, color, user_id, username) { 

        // remove the previous participant select entry
        for(var i=0 ; i < part_select.options.length ; i++) { 
            if(part_select.options[i].value == user_id) { 
                part_select.remove(i);
            }
        }

        part_select.options.add( new Option(username + ' ' + ' ' + board_size + ' ' + main_time + ' ' + komi + ' ' + color , user_id) );
        
        
    }
}


// annoying wrappers for various event handlers
// TODO perhaps there's a better way of accessing NetClient_instance from event handlers?  some kind of singleton technique?

function NetClient_onopen_wrapper() { NetClient_instance.connected(); }
function NetClient_onlinereceived_wrapper(data) { NetClient_instance.onlinereceived(data); }
function NetClient_onclose_wrapper(code) { NetClient_instance.onclose(code); }
function NetClient_onmove_wrapper(data) { NetClient_instance.onmove(data); }
function NetClient_preload(session_key) { NetClient_instance = new NetClient(session_key); }

// init funcs
function NetClient_start() { 
    // TODO the unload event fires but the page always navigates away before orbited gets the PART message sent.. so this is useless until i figure out why
    // window.onunload = NetClient_unload
    addEventListener("unload", NetClient_unload, false);
    NetClient_instance.start(); 
}

function NetClient_unload() { 
    NetClient_instance.unload();
}


/////////////////////////////////////////////////////////////////////////////
// Eidogo loader

// global var to hold the player
var NetClient_eidogo_player = null;

// attached to load event by GameView
function initEidogo() { 
    NetClient_eidogo_player = new eidogo.Player({
        container:       "eidogo",
        // theme:           "compact", // TODO standard or compact should be a player pref or something
        theme:           "standard", // TODO standard or compact should be a player pref or something
        sgf:             eidogo_SGF,
        // sgfPath:         "/static/eidogo/sgf/",
        mode:            "play",
        hooks:           {"createMove": NetClient_onmove_wrapper},
        loadPath:        [0, 0],
        showComments:    true,
        showPlayerInfo:  true,
        showGameInfo:    true,
        showTools:       true,
        showOptions:     true,
        showNavTree:     true,
        markCurrent:     true,
        markVariations:  true,
        markNext:        false,
        enableShortcuts: false,
        problemMode:     false
    });
    
    
    // NetClient_eidogo_player.loadSgf( {'sgf': eidogo_SGF} );
    NetClient_eidogo_player.last();
}





////////////////////////////////////////////////////////////////////
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



