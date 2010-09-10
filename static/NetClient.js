// this is the network client that connects to our real-time server via orbited

// set orbited port
Orbited.settings.port = 8001

// instantiate netclient in to its global
NetClient_instance = new function NetClient() { 

    // debug mode
    this.NetClient_debug = netclient_debug_mode;
    
    // track our session_key
    this.session_key = netclient_session_key;

    // to hold our TCPSocket object
    this.tcp = null;

    // to hold our LineReceiver object
    this.line = null;

    // clear to send flag
    this.cts = true;

    // our send queue
    this.sendq = Array();

    // keep track of which games we are joined
    this.joinedgames = {};

    // keep track of audio samples
    this.audio = {};

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

            sound_button = document.createElement("BUTTON");
            sound_button.innerHTML = "Clicky";
            sound_button.setAttribute("type", "button");
            sound_button.setAttribute("onClick", 'NetClient_instance.onsound(1,1)')
            
            debug_div.appendChild(debug_input);
            debug_div.appendChild(debug_button);
            debug_div.appendChild(sound_button);
            debug_div.appendChild( document.createElement("BR") );
            debug_div.appendChild(debug_textarea);


            document.body.appendChild(debug_div);

            this.debug("NetClient.start - " + window.location.hostname + ":8002\n");
        }

        this.tcp = new Orbited.TCPSocket();
        this.line = new LineProtocol(this.tcp);
        this.line.open(window.location.hostname,8002,false);

        this.line.onopen = function() { NetClient_instance.connected(); }; 
        this.line.onlinereceived = function(data) { NetClient_instance.onlinereceived(data); }; 
        this.line.onclose = function(code) { NetClient_instance.onclose(code); }; 
        
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
            part_select = $("#game_"+game_id+"_ParticipantSelect")[0];

            if(part_select.options[0].value == 0) { 
                part_select.remove(0);
            }
            
            part_select.options.add( new Option(dataAr[1] + ' ('+dataAr[2]+')', dataAr[0]) );

            this.updatecomment(game_id, '*** '+dataAr[1]+' has joined the game');

        } else if(command == "PART") { 

            part_select = $("#game_"+game_id+"_ParticipantSelect")[0];
            
            for(var i=0 ; i < part_select.options.length ; i++) { 
                if(part_select.options[i].value == dataAr[0]) { 
                    part_select.remove(i);
                }
            }
            
            this.updatecomment(game_id, '*** '+dataAr[1]+' has left the game');

        } else if(command == "CMNT") {

            this.updatecomment(game_id, '<'+dataAr[0]+'> '+dataAr[1]);

        } else if(command == "CHAT") {

            this.updatechat(chat_id, '<'+dataAr[0]+'> '+dataAr[1]);

        } else if(command == "MOVE") { 

            iface.eidogoPlayers[ game_id ].doMove(dataAr[0], true, dataAr[1]);

        } else if(command == "NODE") {             

            iface.eidogoPlayers[ game_id ].assignSnProp( dataAr[0] );

        } else if(command == "UNDO") { 

            if(confirm("Opponent requested an undo.  Allow?")) { 
                this.send(["OKUN", game_id]);
            } else { 
                this.send(["NOUN", game_id]);
            }

        } else if(command == "OKUN") { 
            
            alert("Undo accepted");
            iface.eidogoPlayers[ game_id ].back();

        } else if(command == "NOUN") { 

            alert("Undo rejected");
        
        } else if(command == "DEAD") { 

            // translate coord to a point (thats how scoreToggleStone likes it)
            coord = iface.eidogoPlayers[ game_id ].sgfCoordToPoint(dataAr[0]);

            iface.eidogoPlayers[ game_id ].scoreToggleStone( coord.x, coord.y, false );
            
        } else if(command == "OFFR") { 

            this.receivedoffer(game_id, dataAr[0], dataAr[1], dataAr[2], dataAr[3], dataAr[4], dataAr[5]);

        } else if(command == "GVAR") { 
            
            iface.initEidogo(game_id, dataAr[0], dataAr[1], dataAr[2], dataAr[3], dataAr[4], dataAr[5], dataAr[6], dataAr[7], dataAr[8], dataAr[9], dataAr[10], dataAr[11], dataAr[12], dataAr[13], dataAr[14]);

        } else if(command == "GUSR") { 

            iface.updateParticipantList(game_id, dataAr[0])
            
        } else if(command == "BEGN") { 
            
            iface.makeGameTab( game_id, false, true );
            
        } else if(command == "NAVI") { 
            
            this.navi(dataAr);

        } else if(command == "GAME") { 
            
            // our game command was accepted and a new game was created

            iface.onNewGameCreated( game_id );

        } else if(command == "RSLT") { 

            if(typeof(iface.eidogoPlayers[ game_id ]) != "undefined") { 
                iface.eidogoPlayers[ game_id ].setResult( dataAr[0], dataAr[1], dataAr[2]);
            }

        } else if(command == "SYNC") { 
            
            alert("Your client is not synchronized with the server; server said: "+dataAr[0]);

            // window.location.reload();

        } else if(command == "TIME") { 
            
            // make sure that the player exists
            if(typeof(iface.eidogoPlayers[ game_id ]) != "undefined") { 
                iface.eidogoPlayers[ game_id ].updateTimerState( dataAr[0],
                                                                     dataAr[1],
                                                                     dataAr[2],
                                                                     dataAr[3],
                                                                     dataAr[4],
                                                                     dataAr[5] );
            }

        } else if(command == "JCHT") { 

            part_select = $("#chat_"+chat_id+"_ParticipantSelect")[0];

            if(part_select.options[0].value == 0) { 
                part_select.remove(0);
            }

            part_select.options.add( new Option(dataAr[1], dataAr[0]) );
            
            this.updatechat(chat_id, "*** "+dataAr[1]+" has joined the chat" );
            
        } else if(command == "PCHT") {
            
            if( $("#chat_"+chat_id+"_ParticipantSelect")[0] ) { 
                part_select = $("#chat_"+chat_id+"_ParticipantSelect")[0];            

                for(var i=0 ; i < part_select.options.length ; i++) { 
                    if(part_select.options[i].value == dataAr[0]) { 
                        part_select.remove(i);
                    }
                }

                this.updatechat(chat_id, "*** "+dataAr[1]+" has left the chat" );
            }

        } else if(command == "CMNT") {

            this.updatecomment(game_id, '<'+dataAr[0]+'> '+dataAr[1]);
                        
        } else if(command == "SCOR") { 
                        
            var score_w = dataAr[3];
            var score_b = dataAr[7];
            
            if(score_w > score_b) { 
                var result = 'W+' + (score_w - score_b);
            } else { 
                var result = 'B+' + (score_b - score_w);
            }

            this.updatecomment(game_id, 'Opponent submitted score W:'+score_w+' B:'+score_b+' Result:'+result);

        } else { 
            alert("Unknown net command received from server: "+command);
        }
    }

    this.onclose = function(data) { 
        this.debug("NetClient.onclose: " + data + "\n");

        /* TODO we need to be more graceful than this.
        if(confirm('Your connection to the server has been lost, would you like to reconnect?')) { 
            window.location.reload();
        }*/
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
        this.line.reset();
    }
        
    this.debug = function(msg) { 
        curdate = new Date();
        if($("#NetClient_debug")[0])
            $("#NetClient_debug")[0].value += curdate.toLocaleString() + ": " + msg;
        
        // scroll down
        $("#NetClient_debug")[0].scrollTop = $("#NetClient_debug")[0].scrollHeight;
    }

    /////////////////////////////////////////
    // higher level commands

    this.joingame = function(game_id) { 
        
        if(!this.joinedgames[game_id]) { 
            this.joinedgames[game_id] = true;
            this.send( ["JOIN", game_id] );
        } 

        // if we didnt actually join, go ahead and refresh the user list
        this.send( ["GUSR", game_id] );

        // in any case, attempt to get the game vars
        this.send( ["GVAR", game_id] );        
    }

    this.partgame = function(game_id) { 
        // make sure we know we are no longer joined
        this.joinedgames[game_id] = false;
        this.send( ["PART", game_id] );
    }

    this.joinchat = function(chat_id) { 
        this.send( ["JCHT", chat_id] );
    }

    this.partchat = function(chat_id) { 
        this.send( ["PCHT", chat_id] );
    }

    this.chat = function(chat_id, chattext) {
        this.send( ["CHAT", chat_id, chattext] );
    }

    this.updatechat = function(chat_id, msg) { 
        if(ta = $("#chat_"+chat_id+"_Textarea")[0])
            ta.value += msg + "\r\n";        
    }
    
    this.comment = function(game_id, commentinput) {
        this.send( ["CMNT", game_id, commentinput.value] );
        commentinput.value = '';
    }

    this.updatecomment = function(game_id, msg) { 
        if(ta = $("#game_"+game_id+"_CommentTextarea")[0])
            ta.value += msg + "\r\n";
        
        if(typeof(iface.eidogoPlayers[ game_id ]) != "undefined") 
            iface.eidogoPlayers[ game_id ].dom.comments.innerHTML += msg.replace('<','&lt;').replace('>','&gt;') + "<br>";            
    }

    this.onmove = function(game_id, data) { 
        coord = data[0];
        color = data[1];
        sn = data[2]
        
        // TODO support getting a copy of all the comments made since the last move from eidogo
        comments = "";
        
        this.send( ["MOVE", game_id, coord, color, sn, comments] )
    }

    this.ondead = function(game_id, data) { 
        this.send( ["DEAD", game_id, iface.eidogoPlayers[ game_id ].pointToSgfCoord({'x': data[0], 'y': data[1]})] )
    }

    this.onnav = function(game_id, path) { 
        this.send( ["NAVI", game_id, path] );
    }
    
    this.onundo = function(game_id) { 
        this.send( ["UNDO", game_id] );
    }

    this.onsound = function(game_id, coord) { 
        // TODO check for some kind of per-game muting?

        // TODO check for pass and play different noise
        
        numSamples = 4;
        whichClick = Math.floor(Math.random() * (numSamples)) + 1

        this.playsound('/static/audio/click'+whichClick+'.ogg');
    }

    this.playsound = function(file) { 

        if( typeof(this.audio[ file ]) == "undefined" ) { 
            this.audio[ file ] = new Audio( file );
        } else { 
            
            // this next condition warrants some explanation; when you play() an element that 
            // is playing, it will not play because its already playing.  however, the element
            // will also not play if it has just finished playing but has not reset some internal
            // state... if you play() a .5 sec sample, and re-play at .6 seconds, the sample will
            // not replay.  If you put a currentTime = 0 there before the play() to rewind and then
            // play, the sample will play, but delayed by a second or two.  In chrome and in firefox.
            // i dunno why... but this method at least ensures the sound will play.  I put the
            // delete in here in a meager attempt to make sure the browser releases the resources
            // associated to the audio object.  i dont know enough about javascript implementations
            // to know if that's necessary....
            if( ! this.audio[ file ].ended) { 
                delete this.audio[ file ];
                this.audio[ file ] = new Audio( file );
            }

        }
        
   
        this.audio[ file ].play();
    }
    
    this.onresign = function(game_id) { 
        this.send( ["RSGN", game_id] );
    }
    
    this.onscoresubmit = function(game_id, data) {         
        data.unshift(game_id);
        data.unshift("SCOR");
        this.send( data );
    }

    this.creategame = function(type, boardsize, komi, allowundo, maintime, ot_type, ot_period, ot_count) { 
        this.send( ["GAME", type, boardsize, komi, allowundo, maintime, ot_type, ot_period, ot_count] );
    }


    // this func is called when the game owner decides he's ready to start the game
    this.startgame = function(game_id) { 
        parts = $("#game_"+game_id+"_ParticipantSelect")[0];
        selected_user = parts.options[ parts.selectedIndex ].value;

        this.send( ["BEGN", game_id, selected_user ] )
    }

    // this func is called when challenders click the "Offer to Play" button
    this.makeoffer = function(game_id) { 
        board_size = $("#offer_BoardSize").val();
        main_time = $("#offer_MainTime").val();
        komi = $("#offer_Komi").val();
        my_color = $("#offer_Color").val();
        
        this.send( ["OFFR", game_id, board_size, main_time, komi, my_color] )
    }

    // this func is called when an offer is received
    this.receivedoffer = function(game_id, board_size, main_time, komi, color, user_id, username) { 

        part_select = $("#game_"+game_id+"_ParticipantSelect")[0];

        // remove the previous participant select entry
        for(var i=0 ; i < part_select.options.length ; i++) { 
            if(part_select.options[i].value == user_id) { 
                part_select.remove(i);
            }
        }

        part_select.options.add( new Option(username + ' ' + ' ' + board_size + ' ' + main_time + ' ' + komi + ' ' + color , user_id) );        
    }

    this.navi = function(data) { 
        iface.eidogoPlayers[ game_id ].goToNodeWithSN( data[0] );

        // if the player is on restricted nav, we need to make sure that if they are in score mode,
        // that we move them out of it whenever we do a navi, otherwise they get stuck in score mode
        if(iface.eidogoPlayers[ game_id ].owgsRestrictedNav)
            iface.eidogoPlayers[ game_id ].selectTool("play");
    }
}

// start netclient on-load
$( function() { NetClient_instance.start(); } );

// call the netclient unload on unload.  this doesnt work in my browsers but it might work somewhere
$(window).bind('beforeunload', function() { NetClient_instance.unload(); } );


////////////////////////////////////////////////////////////////////
// Below here is lifted from orbited's examples:


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
