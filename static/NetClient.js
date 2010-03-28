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

    this.start = function() { 

        if(NetClient_debug) {
            document.body.innerHTML += "<textarea cols=100 rows=8 id=\"NetClient_debug\"></textarea>";
            this.debug("NetClient.start\n");
        }
                
        tcp = new Orbited.TCPSocket();
        tcp.open('127.0.0.1',8002,false);

        // theres gotta be a cleaner way to do this!
        tcp.onopen = NetClient_onopen_wrapper;
        tcp.onread = NetClient_onread_wrapper;
        tcp.onclose = NetClient_onclose_wrapper;
    }

    this.onread = function(data) { 
        this.debug("RECV: " + data + "\n");

        dataAr = JSON.parse(data);

        this.debug("RECV PARSE: " + JSON.stringify(dataAr) + "\n");

        // if there are pending messages, then paste them 
        if(dataAr[0] == "CTS") {
            if(this.sendq.length > 0) { 
                this.cts = true;
                this.send( this.sendq.pop() );
            }

        } else if(dataAr[0] == "JOIN") { 
            
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
            this.debug("SEND: " + data + "\n");
            this.cts = false;

            // JSON is imported by orbited
            tcp.send(JSON.stringify(data) + "\r\n");
        }
    }

    this.connected = function() { 
        this.debug("NetClient.connected\n");
        
        this.send( ["SESS", this.session_key] );
    }
    
    this.debug = function(msg) { 
        curdate = new Date();
        document.getElementById("NetClient_debug").value += curdate.toLocaleString() + ": " + msg;
    }
    
}


// annoying wrappers for tcpsocket event handlers
function NetClient_onopen_wrapper() { NetClient_instance.connected(); }
function NetClient_onread_wrapper(data) { NetClient_instance.onread(data); }
function NetClient_onclose_wrapper(code) { NetClient_instance.onclose(code); }

// init funcs
function NetClient_start() { NetClient_instance.start(); }
function NetClient_preload(session_key) { NetClient_instance = new NetClient(session_key); }




// This is lifted from orbited's stomp.js STOMP protocol example

// NB: This is loosly based on twisted.protocols.basic.LineReceiver
//     See http://twistedmatrix.com/documents/8.1.0/api/twisted.protocols.basic.LineReceiver.html
// XXX this assumes the lines are UTF-8 encoded.
// XXX this assumes the lines are terminated with a single NL ("\n") character.
LineProtocol = function(transport) {
    var log = getStompLogger("LineProtocol");
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
        log.debug("transport.onread: enter isLineMode=", isLineMode, " buffer[", buffer.length, "]=", buffer, " data[", data.length, "]=", data);

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
                log.debug("fire onlinereceived line[", line.length, "]=", line);
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
            log.debug("fire onrawdatareceived data[", data.length, "]=", data);
            self.onrawdatareceived(data);
        }

        log.debug("transport.onread: leave");
    };

    //
    // Protocol implementation.
    //

    self.setRawMode = function() {
        log.debug("setRawMode");
        isLineMode = false;
    };

    // TODO although this is a nice interface, it will do a extra copy
    //      of the data, a probable better alternative would be to
    //      make onrawdatareceived return the number of consumed bytes
    //      (instead of making it comsume all the given data).
    self.setLineMode = function(extra) {
        log.debug("setLineMode: extra=", extra);
        isLineMode = true;
        if (extra && extra.length > 0)
            transport.onread(extra);
    };

    self.send = function(data) {
        log.debug("send: data=", data);
        return transport.send(data);
    };

    self.open = function(host, port, isBinary) {
        log.debug("open: host=", host, ':', port, ' isBinary=', isBinary);
        transport.open(host, port, isBinary);
    };

    self.close = function() {
        log.debug("close");
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

