// this is the network client that connects to our real-time server via orbited

Orbited.settings.port = 8001

var NetClient_instance;

function NetClient(sessionid) { 
    this.sessionid = sessionid;
	
	this.tcp = null;

	this.start = function() { 
    	tcp = new Orbited.TCPSocket();
	    tcp.open('127.0.0.1',8002,false);

	    tcp.onopen = NetClient_onopen_wrapper;
	    tcp.onread = function(data) { alert('Message: '+data); }
    	tcp.onclose = function(code) { alert('Closed: '+code); }
    }

    this.send = function(data) { 
		// tcpsocket example shows  < 3 ..  but onopen fires before readyState is 3.. it fires when its 2 (OPENING) .. 
        if (tcp.readyState < 3) {
            alert("ERR: Not Connected - ready state " + tcp.readyState );
		} else if (tcp.readyState > 3 ) {
            alert("ERR: Disconnect(ed)(ing)");
        } else {
            tcp.send(data);
            alert("SEND: " + data);
        }
    }

	this.connected = function() { 
		alert('connected');
		// JSON is imported by orbited
		this.send(JSON.stringify(["CONN",this.sessionid])+"\r\n");
    }
}

function NetClient_onopen_wrapper() { 
	NetClient_instance.connected();
}

function NetClient_start() { 
	NetClient_instance.start();
}

function NetClient_preload(sessionid) { 
	NetClient_instance = new NetClient(sessionid);
}