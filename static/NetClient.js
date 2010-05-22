// this is the network client that connects to our real-time server via orbited

Orbited.settings.port = 8001

var NetClient_instance = null;

function NetClient(session_key, debug_mode) { 

    // debug mode
    this.NetClient_debug = debug_mode
    
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

        if(this.NetClient_debug) {
            debug_div = document.createElement("DIV");

            debug_textarea = document.createElement("TEXTAREA");
            debug_textarea.setAttribute("cols", 80);
            debug_textarea.setAttribute("rows", 20);
            debug_textarea.setAttribute("id", "NetClient_debug");

            debug_input = document.createElement("INPUT");
            debug_input.setAttribute("id", "sendraw");
            debug_input.setAttribute("size", "80");
            debug_input.setAttribute("type", "text");       
            
            debug_button = document.createElement("BUTTON");
            debug_button.innerHTML = "Send";
            debug_button.setAttribute("type", "button");
            debug_button.setAttribute("onClick", 'NetClient_instance.sendraw( $("#sendraw").val())')
            
            debug_div.appendChild(debug_input);
            debug_div.appendChild(debug_button);
            debug_div.appendChild( document.createElement("BR") );
            debug_div.appendChild(debug_textarea);

            document.body.appendChild(debug_div);

            this.debug("NetClient.start\n");
        }

        this.tcp = new Orbited.TCPSocket();
        this.line = new LineProtocol(this.tcp);
        this.line.open(window.location.hostname,8002,false);

        // theres gotta be a cleaner way to do this!
        this.line.onopen = NetClient_onopen_wrapper;
        this.line.onlinereceived = NetClient_onlinereceived_wrapper;
        this.line.onclose = NetClient_onclose_wrapper;

    }

    this.onlinereceived = function(line) { 
        this.debug("RECV: " + line + "\n");

        dataAr = Orbited.JSON.parse(line);

        command = dataAr.shift();

        if(dataAr.length > 0) {         
            if( (command == 'JCHT') || 
                (command == 'CHAT') ||
                (command == 'PCHT') ) 
                chat_id = dataAr.shift()
            else
                game_id = dataAr.shift()
        }

        // if there are pending messages, then paste them 
        if(command == "CTS") {

            this.cts = true;
            if(this.sendq.length > 0) { 
                this.send( this.sendq.pop() );
            }

        } else if(command == "JOIN") { 
            part_select = $("#ParticipantSelect")[0];

            if(part_select.options[0].value == 0) { 
                part_select.remove(0);
            }
            
            part_select.options.add( new Option(dataAr[1] + ' ('+dataAr[2]+')', dataAr[0]) );

            this.updatecomment('*** '+dataAr[1]+' has joined the game');

        } else if(command == "PART") { 

            part_select = $("#ParticipantSelect")[0];
            
            for(var i=0 ; i < part_select.options.length ; i++) { 
                if(part_select.options[i].value == dataAr[0]) { 
                    part_select.remove(i);
                }
            }
            
            this.updatecomment('*** '+dataAr[1]+' has left the game');

        } else if(command == "CMNT") {

            this.updatecomment('<'+dataAr[0]+'> '+dataAr[1]);

        } else if(command == "CHAT") {

            this.updatechat('<'+dataAr[0]+'> '+dataAr[1]);

        } else if(command == "MOVE") { 

            NetClient_eidogo_player.doMove(dataAr[0], true, dataAr[1]);

        } else if(command == "NODE") {             

            NetClient_eidogo_player.assignSnProp( dataAr[0] );

        } else if(command == "UNDO") { 

            if(confirm("Opponent requested an undo.  Allow?")) { 
                this.send(["OKUN", game_id]);
            } else { 
                this.send(["NOUN", game_id]);
            }

        } else if(command == "OKUN") { 
            
            alert("Undo accepted");
            NetClient_eidogo_player.back();

        } else if(command == "NOUN") { 

            alert("Undo rejected");
        
        } else if(command == "DEAD") { 

            // translate coord to a point (thats how scoreToggleStone likes it)
            coord = NetClient_eidogo_player.sgfCoordToPoint(dataAr[0]);

            NetClient_eidogo_player.scoreToggleStone( coord.x, coord.y, false );
            
        } else if(command == "OFFR") { 

            this.receivedoffer(dataAr[0], dataAr[1], dataAr[2], dataAr[3], dataAr[4], dataAr[5]);

        } else if(command == "BEGN") { 

            window.location.reload();

        } else if(command == "NAVI") { 
            
            this.navi(dataAr);

        } else if(command == "GAME") { 

            // this command allows the server to update our game state & type.. currently unused
            NetClient_eidogo_player.setGameType( dataAr[0], dataAr[1] );

        } else if(command == "RSLT") { 
            
            NetClient_eidogo_player.setResult( dataAr[0], dataAr[1], dataAr[2]);

        } else if(command == "SYNC") { 
            
            alert("Your client is not synchronized with the server; server said: "+dataAr[0]);

            // window.location.reload();

        } else if(command == "TIME") { 
            
            NetClient_eidogo_player.updateTimerState( dataAr[0],
                                                      dataAr[1],
                                                      dataAr[2],
                                                      dataAr[3],
                                                      dataAr[4],
                                                      dataAr[5] );

        } else if(command == "JCHT") { 

            part_select = $("#ParticipantSelect")[0];

            if(part_select.options[0].value == 0) { 
                part_select.remove(0);
            }

            part_select.options.add( new Option(dataAr[1], dataAr[0]) );
            
            this.updatechat( "*** "+dataAr[1]+" has joined the chat" );
            
        } else if(command == "PCHT") {

            part_select = $("#ParticipantSelect")[0];
            
            for(var i=0 ; i < part_select.options.length ; i++) { 
                if(part_select.options[i].value == dataAr[0]) { 
                    part_select.remove(i);
                }
            }

            this.updatechat( "*** "+dataAr[1]+" has left the chat" );

        } else if(command == "CMNT") {

            this.updatechat('<'+dataAr[0]+'> '+dataAr[1]);
                        
        } else if(command == "SCOR") { 

            // the SCOR command is really only used by bots or for client debugging, this is not information that is pertinent to eidogo / the web interface

        } else { 
            alert("Unknown net command received from server: "+command);
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
            json_out = Orbited.JSON.stringify(data);
            this.debug("SEND: " + json_out + "\n");
            this.cts = false;

            this.tcp.send(json_out + "\r\n");
        }
    }

    // this is a debug function that sends arbitrary strings 
    this.sendraw = function(msg) { 
        this.debug("SENDRAW: " + msg + "\n");
        this.tcp.send(msg + "\r\n");
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
        if($("#NetClient_debug")[0])
            $("#NetClient_debug")[0].value += curdate.toLocaleString() + ": " + msg;
    }

    /////////////////////////////////////////
    // higher level commands

    this.joingame = function(game_id) { 
        this.game_id = game_id;
        this.send( ["JOIN", this.game_id] );
    }

    this.joinchat = function(chat_id) { 
        this.chat_id = chat_id;
        this.send( ["JCHT", this.chat_id] );
    }

    this.chat = function(chatinput) {
        this.send( ["CHAT", this.chat_id, chatinput.value] );
        chatinput.value = '';
    }

    this.updatechat = function(msg) { 
        if(ta = $("#ChatTextarea")[0])
            ta.value += msg + "\r\n";        
    }
    
    this.comment = function(commentinput) {
        this.send( ["CMNT", this.game_id, commentinput.value] );
        commentinput.value = '';
    }

    this.updatecomment = function(msg) { 
        if(ta = $("#CommentTextarea")[0])
            ta.value += msg + "\r\n";
        
        if(NetClient_eidogo_player != null) 
            NetClient_eidogo_player.dom.comments.innerHTML += msg.replace('<','&lt;').replace('>','&gt;') + "<br>";            
    }

    this.onmove = function(data) { 
        coord = data[0];
        color = data[1];
        sn = data[2]
        
        // TODO support getting a copy of all the comments made since the last move from eidogo
        comments = "";
        
        this.send( ["MOVE", this.game_id, coord, color, sn, comments] )
    }

    this.ondead = function(data) { 
        this.send( ["DEAD", this.game_id, NetClient_eidogo_player.pointToSgfCoord({'x': data[0], 'y': data[1]})] )
    }

    this.onnav = function(path) { 
        this.send( ["NAVI", this.game_id, path] );
    }
    
    this.onundo = function() { 
        this.send( ["UNDO", this.game_id] );
    }

    this.onresign = function() { 
        this.send( ["RSGN", this.game_id] );
    }
    
    this.onscoresubmit = function(data) {         
        data.unshift(this.game_id);
        data.unshift("SCOR");
        this.send( data );
    }

    // this func is called when the game owner decides he's ready to start the game
    this.startgame = function(data) { 
        parts = $("#ParticipantSelect")[0];
        selected_user = parts.options[ parts.selectedIndex ].value;

        this.send( ["BEGN", this.game_id, selected_user ] )
    }

    // this func is called when challenders click the "Offer to Play" button
    this.makeoffer = function() { 
        board_size = $("#offer_BoardSize").val();
        main_time = $("#offer_MainTime").val();
        komi = $("#offer_Komi").val();
        my_color = $("#offer_Color").val();
        
        this.send( ["OFFR", this.game_id, board_size, main_time, komi, my_color] )
    }

    // this func loads game vars from the server and returns them
    this.getgamevariables = function() { 
        this.send( ["GVAR", self.game_id] );
    }

    // this func is called when an offer is received
    this.receivedoffer = function(board_size, main_time, komi, color, user_id, username) { 

        part_select = $("#ParticipantSelect")[0];

        // remove the previous participant select entry
        for(var i=0 ; i < part_select.options.length ; i++) { 
            if(part_select.options[i].value == user_id) { 
                part_select.remove(i);
            }
        }

        part_select.options.add( new Option(username + ' ' + ' ' + board_size + ' ' + main_time + ' ' + komi + ' ' + color , user_id) );        
    }

    this.navi = function(data) { 
        NetClient_eidogo_player.goToNodeWithSN( data[0] );

        // if the player is on restricted nav, we need to make sure that if they are in score mode,
        // that we move them out of it whenever we do a navi, otherwise they get stuck in score mode
        if(NetClient_eidogo_player.owgsRestrictedNav)
            NetClient_eidogo_player.selectTool("play");
    }
}


// annoying wrappers for various event handlers

// TODO perhaps there's a better way of accessing NetClient_instance from event handlers?  some kind of singleton technique?
function NetClient_onopen_wrapper() { NetClient_instance.connected(); }
function NetClient_onlinereceived_wrapper(data) { NetClient_instance.onlinereceived(data); }
function NetClient_onclose_wrapper(code) { NetClient_instance.onclose(code); }
function NetClient_onmove_wrapper(data) { NetClient_instance.onmove(data); }
function NetClient_ondead_wrapper(data) { NetClient_instance.ondead(data); }
function NetClient_onnav_wrapper(data) { NetClient_instance.onnav(data); }
function NetClient_onundo_wrapper(data) { NetClient_instance.onundo(data); }
function NetClient_onresign_wrapper(data) { NetClient_instance.onresign(data); }
function NetClient_onscoresubmit_wrapper(data) { NetClient_instance.onscoresubmit(data); }
function NetClient_ontime_wrapper(data) { NetClient_instance.ontime(data); }
function NetClient_preload(session_key, debug_mode) { NetClient_instance = new NetClient(session_key, debug_mode); }

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
function initEidogo(game_id) { 

    if(eidogo_owgs_vars["EidogoPlayerStyle"] == "C") 
        use_theme = "compact"
    else
        use_theme = "standard"

    // type: showTools showOptions    
    NetClient_eidogo_player = new eidogo.Player({
        container:       "eidogo",
        theme:           use_theme, // TODO standard or compact should be a player pref or something
        theme:           "standard", // TODO standard or compact should be a player pref or something
        sgf:             eidogo_owgs_vars["sgf"],
        // sgfPath:         "/static/eidogo/sgf/",
        mode:            "play",
        hooks:           {"owgs_createMove": NetClient_onmove_wrapper,
                          "owgs_scoreToggleStone": NetClient_ondead_wrapper,
                          "owgs_nav": NetClient_onnav_wrapper,
                          "owgs_undo": NetClient_onundo_wrapper,
                          "owgs_resign": NetClient_onresign_wrapper,
                          "owgs_scoresubmit": NetClient_onscoresubmit_wrapper,
                         },
        loadPath:        [0, 0],
        markCurrent:     true,
        markVariations:  true,
        markNext:        false,
        enableShortcuts: false,
        problemMode:     false,
        allowUndo:       true,
        owgsNetMode:     true
    });
    
    NetClient_eidogo_player.setGameType( eidogo_owgs_vars["gameType"], 
                                         eidogo_owgs_vars["gameState"] );
        
    NetClient_eidogo_player.setTimerType( eidogo_owgs_vars["gameMainTime"],
                                          eidogo_owgs_vars["gameOvertimeType"],
                                          eidogo_owgs_vars["gameOvertimePeriod"],
                                          eidogo_owgs_vars["gameOvertimeCount"] );
    
    NetClient_eidogo_player.updateTimerState( eidogo_owgs_vars["gameIsOvertimeW"],
                                              eidogo_owgs_vars["gameIsOvertimeB"],
                                              eidogo_owgs_vars["gameOvertimeCountW"],
                                              eidogo_owgs_vars["gameOvertimeCountB"],
                                              eidogo_owgs_vars["gameTimePeriodRemainW"],
                                              eidogo_owgs_vars["gameTimePeriodRemainB"] );

    // initialize timer for both colors
    NetClient_eidogo_player.timerTick('W');
    NetClient_eidogo_player.timerTick('B');

    if(typeof(eidogo_owgs_vars["focusNode"]) != "undefined")
        NetClient_eidogo_player.goToNodeWithSN( eidogo_owgs_vars["focusNode"] );
    else 
        NetClient_eidogo_player.last();

    NetClient_eidogo_player.checkForDoublePass();
    
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

