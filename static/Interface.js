
var interface_tabs = Array();

var tabs = false;

iface = new function Interface() { 

    this.tabCloseCallbacks = Array();

    // store what chats are open in which tabs
    this.chatTabs = Array();

    // store what games are open in which tabs
    this.gameTabs = Array();

    this.openChatTab = function(chat_id) { 

        // if this chat is already open, then just go to the already-opened tab
        if(this.chatTabs[ chat_id ]) { 
            $tabs.tabs('select', this.chatTabs[ chat_id ]);
            return;
        }

        // if a chat ID was not passed the default chat is 1
        if(typeof(chat_id) == "undefined") {
            chat_id = 1;
        }

        // create chat tab for this chat
        $("#ifacetabs").tabs('add', '/chat/'+chat_id, 'Chat #'+chat_id); 

        var tab_index = $tabs.tabs('option', 'selected');

        this.registerTabCloseCallback( tab_index,
                                       function() { 
                                           iface.chatTabs[ chat_id ] = false; 
                                           NetClient_instance.partchat( chat_id ); 
                                       } );

        // store the tab index in chatTabs so we know whats opened where
        this.chatTabs[ chat_id ] = tab_index;

        // join the chat 
        NetClient_instance.joinchat( chat_id );
    },

    this.openGameTab = function(game_id) { 
        $("#ifacetabs").tabs('add', '/games/view/'+game_id, 'Game #'+game_id);
        
        // make us join the game on the server
        NetClient_instance.joingame( game_id );

        // get the game variables from the server
        // eidogo_owgs_vars = NetClient_instance.getgamevariables( game_id );  

        // now load the game variables and init eidogo
        // initEidogo( game_id, eidogo_owgs_vars );

        // MORE NOTES FOR LATER:

        // * It will be a big priority to make NetClient understand that it isnt only tracking 
        //   one game per instance anymore!  not one chat per instance too! (doing that first)

        // * all participants lists need to co-exist.. all eidogo players need to co-exist.. the
        //   html elements ALL need unique IDs!! and netclient has to use them!!!! 

        // * Implement getgamevariables in a *blocking* fashion, we need the game vars *NOW!* 
        //   - not sure how im going to do this..

        // * now that eidogo has been passed all the game variables
        //   PREVENT IT FROM TRYING TO LOAD THEM FROM THE OLD eidogo_owgs_vars GLOBAL!  IT WONT WORK!
    },

    this.closeTab = function(index) {
        // execute the callback, then clear the callback, if there is one
        if(this.tabCloseCallbacks[index]) { 
            this.tabCloseCallbacks[index]();
            this.tabCloseCallbacks[index] = false;
        }

		$tabs.tabs('remove', index);
    },
    
    this.registerTabCloseCallback = function(index, callback) { 
        this.tabCloseCallbacks[index] = callback;
    },

    this.createGame = function() { 
        NetClient_instance.creategame(
            $("#id_Type").val(),
            $("#id_BoardSize").val(),
            $("#id_Komi").val(),
            $("#id_AllowUndo").val() == "on" ? 1 : 0,
            $("#id_MainTime").val(),
            $("#id_OvertimeType").val() ,
            $("#id_OvertimePeriod").val(),
            $("#id_OvertimeCount").val() );
        this.closeTab( $tabs.tabs('option','selected') );
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
        },
        
        // set up the tab template with the close button
        tabTemplate: '<li><a href="#{href}">#{label}</a> <span class="ui-icon ui-icon-close">Remove Tab</span></li>',
    } );
    
    // tab close click event
	$('#ifacetabs span.ui-icon-close').live('click', 
                                            function() { 
                                                index = $('li',$tabs).index($(this).parent());
                                                iface.closeTab(index);
                                            });
});