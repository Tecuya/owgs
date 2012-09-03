

(function() { 

    iface = new function Interface() { 

        // global so we can always get to our eidogo instances
        this.eidogoPlayers = [];

        // stores events that will be executed upon tab open/close events
        this.tabOpenCallback = [];
        this.tabCloseCallback = [];

        // store what chats are open in which tabs
        this.chatTabs = [];

        // store what games are open in which tabs
        this.gameTabs = [];

        // when create game is clicked this stores the tab index so we know, 
        // once we get the GAME command back, which tab to open it in
        this.pendingGameTab = false;

        // this tracks if we already have a login/registration tab open
        this.loginTab = false;
        this.registrationTab = false;

        // this tracks where we have game lists
        this.gameLists = {};

        this.openLogin = function() { 
            // if a login tab is already open just focus is
            if(this.loginTab != false) { 
                $tabs.tabs('select', this.loginTab);
                return;
            }
            
            $("#ifacetabs").tabs('add', '/t/owgs_login.html', 'Log In');

            this.loginTab = $tabs.tabs('option', 'selected');
            
            // bind handler once the form is ready
            this.registerTabOpenCallback( 
                this.loginTab,
                function() {
                    $('#login_form > #login_button').click(
                        function() { 
                            $('#login_status')
                                .html('Logging in....')
                                .css('color','gray');

                            owgs.login( 
                                $('#login_form > #username').val(),
                                $('#login_form > #password').val(),
                                $('#login_form > div > input[name="csrfmiddlewaretoken"]').val());
                        });
                });
            
            this.registerTabCloseCallback( this.loginTab,
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

            // store the tab index in chatTabs so we know whats opened
            // where.  this also causes the tab load event to run the
            // netclient joinchat func after the tab loads

            this.chatTabs[ chat_id ] = tab_index;
            this.registerTabOpenCallback( tab_index,
                                          function() { 
                                              owgs.joinchat( chat_id ) 
                                          });
            
            this.registerTabCloseCallback( tab_index,
                                           function() { 
                                               iface.chatTabs[ chat_id ] = false; 
                                               owgs.partchat( chat_id ); 
                                           } );
        },

        this.makeRegistrationTab = function() { 

            // if a reg tab is already open just focus is
            if(this.registrationTab != false) { 
                $tabs.tabs('select', this.registrationTab);
                return;
            }
            
            $('#ifacetabs').tabs('add', '/static/owgs/registration.html', 'Register');

            var tab_index = $tabs.tabs('option', 'selected');

            // store the index so we may reference the tab later
            this.registrationTab = tab_index;

            // register submit button click on load
            this.registerTabOpenCallback( 
                tab_index,

                function() {
                    $('#registration_submit').click(
                        function() { 

                            $('#registration_error').empty();
                            
                            var doerror = function( errtext ) { 
                                $('#registration_error').append( 
                                    $(document.createElement('div')).text(errtext) );
                            };
                            
                            var pw1 = $('#registration > input[name="password1"]').val();
                            var pw2 = $('#registration > input[name="password2"]').val();

                            if(pw1 != pw2) { 
                                doerror('Password and Confirm Password do not match.');
                                return;
                            }

                            var fdata = {};

                            $.each(
                                [
                                    ['username', 'Username'],
                                    ['email', 'Email'],
                                    ['password1', 'Password'], 
                                ],
                                function(idx,val) { 
                                    
                                    var vv = $('#registration > input[name="'+val[0]+'"]').val();

                                    if( vv.length == 0) { 
                                        doerror(val[1]+' is required.');
                                    }
                                    
                                    fdata[val[0]] = vv;
                                });

                            // if no errors appear, clear to register
                            if( $('#registration_error').find('div').length == 0 ) { 

                                owgs.register( fdata['username'],
                                               fdata['email'],
                                               fdata['password1'] );
                            }
                        });
            });

            this.registerTabCloseCallback( tab_index,
                                           function() { 
                                               iface.registrationTab = false;
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

        this.makeGameTab = function(game_id, in_tab, reloading) {

            if( (typeof(this.gameTabs[ game_id ]) != "undefined") && 
                (this.gameTabs[ game_id ] != false) ) { 
                $tabs.tabs('select', this.gameTabs[ game_id ]);

                // if we arent reloading then we are done!
                if(typeof(reloading) == "undefined") { 
                    return;
                }

                in_tab = this.gameTabs[ game_id ];
            }

            if(in_tab) { 
                this.newTabTarget( in_tab, '/games/view/'+game_id, 'Game #'+game_id);
            } else { 
                $("#ifacetabs").tabs('add', '/games/view/'+game_id, 'Game #'+game_id);
                in_tab = $("#ifacetabs").tabs('option', 'selected');
            }

            // if this is a reloading call, theres no need to re-set the stuff below
            if(typeof(reloading) != "undefined") { 
                return;
            }

            // this causes the tab load event to run the netclient joingame func after the tab loads
            iface.gameTabs[ game_id ] = in_tab;
            this.registerTabOpenCallback( in_tab,
                                          function() { 
                                              owgs.joingame( game_id );
                                          });

            this.registerTabCloseCallback( in_tab,
                                           function() { 
                                               iface.gameTabs[ game_id ] = false; 
                                               owgs.partgame( game_id ); 
                                           } );
        },

        this.closeTab = function(index) {
            // execute the callback, then clear the callback, if there is one
            if(this.tabCloseCallback[index]) { 
                this.tabCloseCallback[index]();
                this.tabCloseCallback[index] = false;
            }

		    $tabs.tabs('remove', index);
        },
        
        this.registerTabCloseCallback = function(index, callback) { 
            this.tabCloseCallback[index] = callback;
        },

        this.registerTabOpenCallback = function(index, callback) { 
            this.tabOpenCallback[index] = callback;            
        },

        this.createGame = function() { 

            // validate me!

            owgs.creategame(
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

        this.makeGameListTab = function(type) { 

            if( (typeof(this.gameLists[ type ]) != "undefined") &&
                (this.gameLists[ type ] != false) ) { 

                $tabs.tabs('select', this.gameLists[ type ]);
                in_tab = this.gameLists[ type ];

            } else { 

                if(type == 'active') { 
                    $("#ifacetabs").tabs('add', '/games/active', 'Active Games');
                } else if(type == 'archive') { 
                    $("#ifacetabs").tabs('add', '/games/archive', 'Archived Games');
                }
                
                in_tab = $("#ifacetabs").tabs('option', 'selected');
                this.gameLists[ type ] = in_tab;
            }

            this.registerTabCloseCallback( in_tab, 
                                           function() { 
                                               iface.gameLists[ type ] = false;
                                           } );
        },


        this.reloadGameList = function() { 
            current_tab = $("#ifacetabs").tabs('option', 'selected');

            if(iface.gameLists["active"] == current_tab) { 
                this.newTabTarget( current_tab, '/games/active', 'Active Games' );
            } else if(iface.gameLists["archive"] == current_tab) { 
                this.newTabTarget( current_tab, '/games/archive', 'Archived Games' );
            }
        },


        this.updateParticipantList = function(game_id, userList) { 
            part_select = $("#game_"+game_id+"_ParticipantSelect")[0];
            for(var i=0;i<part_select.length;i++) { 
                part_select.remove(i);
            }

            for(i=0;i<userList.length;i++) { 
                u = userList[i];
                part_select.options.add( new Option( u[1]+'('+u[2]+')', u[0]) );
            }
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
                hooks:           {"owgs_createMove": function(data) { owgs.onmove( game_id, data ); },
                                  "owgs_scoreToggleStone": function(data) { owgs.ondead( game_id, data); },
                                  "owgs_nav": function(data) { owgs.onnav( game_id, data); },
                                  "owgs_undo": function(data) { owgs.onundo( game_id ); }, 
                                  "owgs_stoneSound": function(data) { owgs.onsound( game_id, data ); },
                                  "owgs_resign": function(data) { owgs.onresign( game_id ); },
                                  "owgs_scoresubmit": function(data) { owgs.onscoresubmit( game_id, data); } },
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
                                 // look at the type of tab that was
                                 // loaded and run whatever NetClient
                                 // commands are appropriate

                                 if( iface.tabOpenCallback[ui.index] !== undefined) { 
                                     iface.tabOpenCallback[ ui.index ]( ui.index );
                                 }
                                 
                                 // var i;
                                 // for(i=0;i<iface.chatTabs.length;i++) {
                                 //     if(iface.chatTabs[i] == ui.index) { 
                                 //         owgs.joinchat( i );
                                 //         break;
                                 //     }
                                 // }

                                 // for(i=0;i<iface.gameTabs.length;i++) {
                                 //     if(iface.gameTabs[i] == ui.index) { 
                                 //         owgs.joingame( i );
                                 //         break;
                                 //     }
                                 // }
                                 

                             });

        // if the fragment selector (http://URL.com#thisthing) 
        if( window.location.href.match(/#login/) ) { 
            iface.openLogin();
        }
        

        // scan get variables and see if they want us to do anything

        var qsParm = new Array();
        
        var query = window.location.search.substring(1);
        var parms = query.split('&');
        for (var i=0; i<parms.length; i++) {
            var pos = parms[i].indexOf('=');
            if (pos > 0) {
                var key = parms[i].substring(0,pos);
                var val = parms[i].substring(pos+1);
                qsParm[key] = val;
            }
        }
        
        if(qsParm["joinGame"]) { 
            var joingames = qsParm["joinGame"].split(",");
            
            for(var i=0;i<joingames.length;i++) { 
                iface.makeGameTab( joingames[i] );
            }
            
        }
        
    });
})();
