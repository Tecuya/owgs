
var interface_tabs = Array();

var tabs = false;

iface = new function Interface() { 

    this.tabCloseCallbacks = Array();

    this.openChatTab = function(chat_id) { 

        // if a chat ID was not passed the default chat is 1
        if(typeof(chat_id) == "undefined") {
            chat_id = 1;
        }

        // create chat tab for this chat
        $("#ifacetabs").tabs('add', '/chat/'+chat_id, 'Chat #'+chat_id); 

        this.registerTabCloseCallback( $tabs.tabs('option', 'selected'),
                                       function() { NetClient_instance.partchat( chat_id ); } );
        
        // join the chat 
        NetClient_instance.joinchat( chat_id );
    },

    this.openViewGameTab = function(game_id) { 
        $("#ifacetabs").tabs('add', '/games/view/'+game_id, 'Game #'+game_id);
        
        // make us join the game on the server
        NetClient_instance.joingame( game_id );

        // get the game variables from the server
        // eidogo_owgs_vars = NetClient_instance.getgamevariables( game_id );  

        // now load the game variables and init eidogo
        // initEidogo( game_id, eidogo_owgs_vars );

        // MORE NOTES FOR LATER:

        // * It will be a big priority to make NetClient understand that it isnt only tracking 
        // one game per instance anymore!  not one chat per instance too! (doing that first)

        // * all participants lists need to co-exist.. all eidogo players need to co-exist.. the
        //   html elements ALL need unique IDs!! and netclient has to use them!!!! 

        // * Implement getgamevariables in a *blocking* fashion, we need the game vars *NOW!* 
        //   - not sure how im going to do this..

        // * now that eidogo has been passed all the game variables
        //   PREVENT IT FROM TRYING TO LOAD THEM FROM THE OLD eidogo_owgs_vars GLOBAL!  IT WONT WORK!
    },

    this.tabClosed = function(index) {
        // call the callback if its set
        if(this.tabCloseCallbacks[index]) { 
            this.tabCloseCallbacks[index]();
        }
        // now clear the callback so it doesnt get called again when this index is reused
        this.tabCloseCallbacks[index] = false;
    },
    
    this.registerTabCloseCallback = function(index, callback) { 
        this.tabCloseCallbacks[index] = callback;
    }
}


// init jquery-ui tabs
$(function() { 
    // set up tabs with sortable
    $("#ifacetabs").tabs().find(".ui-tabs-nav").sortable({axis:'x'});

    // don't reload ajax tab contents every click
    $("#ifacetabs").tabs({cache: true});

    $tabs = $("#ifacetabs").tabs( { 
        add: function(event, ui) {
            // immediately select tabs that we just opened
            $tabs.tabs('select', '#' + ui.panel.id);
            
            // store the tab index and div id in the interface_tabs array for use later
            interface_tabs[ $tabs.tabs('option', 'selected') ] = ui.panel.id;
        },
        
        // set up the tab template with the close button
        tabTemplate: '<li><a href="#{href}">#{label}</a> <span class="ui-icon ui-icon-close">Remove Tab</span></li>',
    } );
    
    // tab close click event
	$('#ifacetabs span.ui-icon-close').live('click', function() {
		var index = $('li',$tabs).index($(this).parent());
        
		$tabs.tabs('remove', index);
        
        iface.tabClosed(index);
	});
    
});
