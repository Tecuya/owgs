

iface = new function Interface() { 

    // global so we can always get to our eidogo instances
    this.eidogoPlayers = Array();

    this.tabCloseCallbacks = Array();

    // store what chats are open in which tabs
    this.chatTabs = Array();

    // store what games are open in which tabs
    this.gameTabs = Array();

    // when create game is clicked this stores the tab index so we know, 
    // once we get the GAME command back, which tab to open it in
    this.pendingGameTab = false;

    // this tracks if we already have a login tab open
    this.loginTab = false;

    this.openLogin = function() { 
        // if a login tab is already open just focus is
        if(this.loginTab != false) { 
            $tabs.tabs('select', this.loginTab);
            return;
        }
             
        $("#ifacetabs").tabs('add', '/accounts/login', 'Log In');

        var tab_index = $tabs.tabs('option', 'selected');

        this.loginTab = tab_index;
        
        this.registerTabCloseCallback( tab_index,
                                       function() { 
                                           iface.loginTab = false;
                                       } );        
    },

    this.makeChatTab = function(chat_id) { 

        // if this chat is already open, then just go to the already-opened tab
        if( (typeof(this.chatTabs[ chat_id ]) != "undefined") && 
            (this.chatTabs[ chat_id ] != false) ) { 
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

        // store the tab index in chatTabs so we know whats opened where.
        // this also causes the tab load event to run the netclient joinchat func after the tab loads
        this.chatTabs[ chat_id ] = tab_index;

        this.registerTabCloseCallback( tab_index,
                                       function() { 
                                           iface.chatTabs[ chat_id ] = false; 
                                           NetClient_instance.partchat( chat_id ); 
                                       } );
    },

    this.onNewGameCreated = function( game_id ) {

        // if for whatever reason we couldnt resolve the tab index to load into, just open a new tab
        if( (!this.pendingGameTab) || (this.pendingGameTab > $tabs.tabs('length'))) {
            this.makeGameTab( game_id, false );
        } else { 
            this.makeGameTab( game_id, this.pendingGameTab );
        }

        // reset pendingGameTab
        this.pendingGameTab = false;
    },

    this.newTabTarget = function( index, url, label ) { 
        $tabs.tabs('label', index, label );
        $tabs.tabs('url', index, url );
        $tabs.tabs('load', index );
    },

    this.makeGameTab = function(game_id, in_tab, force_reload) {

        if( (typeof(this.gameTabs[ game_id ]) != "undefined") && 
            (this.gameTabs[ game_id ] != false) ) { 
            $tabs.tabs('select', this.gameTabs[ game_id ]);            
            if(!force_reload)
                return;
        }

        if(in_tab) { 
            this.newTabTarget( in_tab, '/games/view/'+game_id, 'Game #'+game_id);
        } else { 
            $("#ifacetabs").tabs('add', '/games/view/'+game_id, 'Game #'+game_id);
            in_tab = $("#ifacetabs").tabs('option', 'selected');;
        }

        // this causes the tab load event to run the netclient joingame func after the tab loads
        this.gameTabs[ game_id ] = in_tab;

        this.registerTabCloseCallback( in_tab,
                                       function() { 
                                           iface.gameTabs[ game_id ] = false; 
                                           NetClient_instance.partgame( game_id ); 
                                       } );
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

        // validate me!

        NetClient_instance.creategame(
            $("#id_Type").val(),
            $("#id_BoardSize").val(),
            $("#id_Komi").val(),
            $("#id_AllowUndo").val() == "on" ? 1 : 0,
            $("#id_MainTime").val(),
            $("#id_OvertimeType").val() ,
            $("#id_OvertimePeriod").val(),
            $("#id_OvertimeCount").val() );        
        
        this.pendingGameTab = $tabs.tabs('option', 'selected');
    },

    this.initEidogo = function(game_id, sgf, myColor, type, state, mainTime, overtimeType, overtimePeriod, overtimeCount, isOvertimeW, isOvertimeB, overtimeCountW, overtimeCountB, timePeriodRemainW, timePeriodRemainB, focusNode) { 

        // TODO - make this load real player preferences somehow!
        // use_theme = "compact"            
        use_theme = "standard"

        // type: showTools showOptions    
        this.eidogoPlayers[ game_id ] = new eidogo.Player({
            container:       "game_"+game_id+"_eidogo",
            theme:           use_theme, // TODO standard or compact should be a player pref or something
            sgf:             sgf,
            mode:            "play",
            hooks:           {"owgs_createMove": function(data) { NetClient_instance.onmove( game_id, data ); },
                              "owgs_scoreToggleStone": function(data) { NetClient_instance.ondead( game_id, data); },
                              "owgs_nav": function(data) { NetClient_instance.onnav( game_id, data); },
                              "owgs_undo": function(data) { NetClient_instance.onundo( game_id ); }, 
                              "owgs_resign": function(data) { NetClient_instance.onresign( game_id ); },
                              "owgs_scoresubmit": function(data) { NetClient_instance.onscoresubmit( game_id, data); } },
            loadPath:        [0, 0],
            markCurrent:     true,
            markVariations:  true,
            markNext:        false,
            enableShortcuts: false,
            problemMode:     false,
            allowUndo:       true,
            owgsNetMode:     true,
            owgsColor:       myColor,
            owgsGameID:      game_id

        });
        
        this.eidogoPlayers[ game_id ].setGameType( type,
                                                   state );
        
        this.eidogoPlayers[ game_id ].setTimerType( mainTime,
                                                    overtimeType,
                                                    overtimePeriod,
                                                    overtimeCount );
        
        this.eidogoPlayers[ game_id ].updateTimerState( isOvertimeW,
                                                        isOvertimeB,
                                                        overtimeCountW,
                                                        overtimeCountB,
                                                        timePeriodRemainW,
                                                        timePeriodRemainB );

        // initialize timer for both colors
        this.eidogoPlayers[ game_id ].timerTick('W');
        this.eidogoPlayers[ game_id ].timerTick('B');

        if(focusNode)
            this.eidogoPlayers[ game_id ].goToNodeWithSN( focusNode );
        else 
            this.eidogoPlayers[ game_id ].last();

        this.eidogoPlayers[ game_id ].checkForDoublePass();       
    }


}


// init jquery-ui tabs
$(function() { 
    // set up tabs with sortable
    $("#ifacetabs").tabs().find(".ui-tabs-nav").sortable({axis:'x'});

    // don't reload ajax tab contents every click
    $("#ifacetabs").tabs({cache: true});

    // immediately select new tabs, also create close button template
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


    // tab load event
    $('#ifacetabs').bind('tabsload', 
                         function(event, ui) { 
                             // look at the type of tab that was loaded and run whatever NetClient commands are appropriate 
                             var i;
                             for(i=0;i<iface.chatTabs.length;i++) {
                                 if(iface.chatTabs[i] == ui.index) { 
                                     NetClient_instance.joinchat( i );
                                     break;
                                 }
                             }

                             for(i=0;i<iface.gameTabs.length;i++) {
                                 if(iface.gameTabs[i] == ui.index) { 
                                     NetClient_instance.joingame( i );
                                     break;
                                 }
                             }
                         });

    // if the fragment selector (http://URL.com#thisthing) 
    if( window.location.href.match(/#login/) ) { 
        iface.openLogin();
    }
    
});


