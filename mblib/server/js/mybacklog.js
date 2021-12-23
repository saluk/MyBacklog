const fmtstr = "H:m:s YYYY-MM-DD"
const fmt_datetime = "MMM DD, YYYY, h:mm A"
"1:8:9 2021-09-30"
const luxonfmt = "H:m:s yyyy-LL-dd"

function pad(num) {
    var s = "" + num;
    if(s.length<2) {
        s = "00" + num;
        return s.substr(s.length-2);
    }
    return s;
}

playtime_to_hour_min_sec = function(pt) {
    var dur = moment.duration({'seconds':pt});
    var hours = Math.floor(dur.as('hours'));
    var minutes = Math.floor(dur.as('minutes')-hours*60);
    var seconds = Math.floor(dur.as('seconds')-hours*60*60-minutes*60);
    return pad(hours)+":"+pad(minutes)+":"+pad(seconds);
}

hour_min_sec_to_playtime = function(hour_sec) {
    var dur = moment.duration(hour_sec);
    return dur.as('seconds');
}

to_local_string = function(timestamp) {
    return luxon.DateTime.fromFormat(timestamp, luxonfmt)
        .setZone('UTC', {keepLocalTime: true})
        .setZone('local').toString()
}

to_timestamp = function(local_string) {
    return luxon.DateTime.fromISO(local_string).toLocal().setZone('UTC').toFormat(luxonfmt)
}

var params = new URLSearchParams(window.location.search);
var username = params.get("username");

var app = new Vue({
    el: '#game_list',
    data: {
        load_games_state: true,
        username: username,
        games: [],
        edit_game: null,
        sources: [],
        name_filter: '',
        source_selected: '',
        finished_filter: '',
        finished_options: [{
            'value': '',
            text: 'All States'
        }, {
            'value': 0,
            'text': 'Unfinished'
        }, {
            'value': 1,
            'text': 'Finished'
        }],
        games_length: 0,
        currentPage: 1,
        perPage: 30,
        loaded_index: 0,
        img: function(game) {
            if (!game.images || !game.images.length) {
                return '';
            }
            return game.images[0]['url'];
        },
        src: function(game) {
            if (!game.sources) {
                return '';
            }
            return game.sources[0]['source'];
        },
        row_color: function(game) {
            if(game.finished){
                return 'bg-success';
            }
            return 'bg-info';
        },
        nice_time: function(game) {
            return playtime_to_hour_min_sec(game.playtime);
        },
        nice_date: function(game) {
            if(!game.lastplayed) {
                return 'never'
            }
            var dt = moment.utc(game.lastplayed,fmtstr);
            return dt.fromNow();
        },
        get_game_page: function(reset = false) {
            var start = (this.currentPage - 1) * this.perPage;
            var end = start + this.perPage;
            if (this.loaded_index != start || reset) {
                load_games(start, this.perPage);
            }
            return this.games;
        },
        add_name: '',
        add_source: '',
        add_nowplayed: 'nowplayed'
    },
    computed: {
        rows() {
            return this.games_length;
        },
        e_playtime: {
            get() {
                console.log('getting')
                console.log(this.edit_game.playtime);
                console.log(this.nice_time(this.edit_game));
                return this.nice_time(this.edit_game);
            },
            set(v) {
                console.log('setting '+v);
                this.edit_game.playtime = hour_min_sec_to_playtime(v);
            }
        }
    },
    methods: {
        dosearch() {
            this.get_game_page(true);
        },
        add_game() {
            if (!this.add_name || !this.add_source) {
                return;
            }
            this.$bvToast.toast(message = 'Adding ' + this.add_name,
                options = {
                    title: 'Adding Game',
                    autoHideDelay: 1000
                });
            add_game(this.add_name, this.add_source, this.add_nowplayed);
            //this.add_name = '';
            //this.add_source = '';
        },
        set_edit_game(game) {
            this.edit_game = game;
            this.edit_game.lastplayed_local = to_local_string(game.lastplayed)
            this.edit_game.finish_date_local = to_local_string(game.finish_date)
            this.edit_game.import_date_local = to_local_string(game.import_date)
        },
        clear_edit_game() {
            if(this.edit_game){
                this.edit_game = null;
            }
            this.$bvModal.hide('edit_game_other');
        },
        set_time_modal(game) {
            this.set_edit_game(game);
            this.$bvModal.show('edit_game_playtime');
        },
        set_lastplayed_modal(game) {
            this.set_edit_game(game);
            this.$bvModal.show('edit_game_lastplayed');
        },
        edit_modal(game) {
            this.set_edit_game(game);
            this.$bvModal.show('edit_game_other');
        },
        playing_modal(game, init_request=true) {
            this.clear_edit_game();
            if(init_request){
                games_method(game, 'start_playing_game');
            }
            this.set_edit_game(game);
            this.edit_game.is_playing = true;
            this.$bvModal.show('playing_game');
        },
        end_playing_modal() {
            this.edit_game.is_playing = false;
            games_method(this.edit_game, 'stop_playing_game');
        },
        update_playtime(v) {
            var playtime = hour_min_sec_to_playtime(v);
            this.edit_game.playtime = playtime;
        },
        send_game_updates() {
            console.log(this.edit_game.lastplayed_local)
            this.edit_game.lastplayed = to_timestamp(this.edit_game.lastplayed_local)
            this.edit_game.finish_date = to_timestamp(this.edit_game.finish_date_local)
            this.edit_game.import_date = to_timestamp(this.edit_game.import_date_local)
            game_submit(this.edit_game, "rawdata", this.edit_game);
        },
        update_screenshots(source) {
            update_screenshots(source);
        }
    }
});

var img = function(game) {}

console.debug(app.$data);

let cancelSource = null;

load_games = function(start = 0, count = 50) {
    if (cancelSource) {
        cancelSource.cancel();
    }
    cancelSource = axios.CancelToken.source();
    app.load_games_state = true;
    axios.get('/list?start=' + start + '&count=' + count + '&user=' + app.username + '&source_filter=' + app.source_selected + '&finished_filter=' + app.finished_filter + '&name_filter=' + app.name_filter, {
            cancelToken: cancelSource.token
        })
        .then(function(response) {
            console.log(response.data);
            app.games = response.data.games;
            app.games_length = response.data.length;
            app.loaded_index = start;
            if(response.data.playing){
                app.playing_modal(response.data.playing.game, false);
            }
        })
        .catch(function(error) {
            if (axios.isCancel(error)) {
                return;
            }
            console.log(error);
        })
        .finally(function() {
            app.load_games_state = false;
        })
};

load_sources = function() {
    axios.get('/sources?user=' + app.username)
        .then(function(response) {
            var sources = [{
                value: '',
                text: 'all sources',
                selected: true
            }];
            for (var key in response.data) {
                sources.push({
                    value: key,
                    text: key
                });
            }
            app.sources = sources;
        })
        .catch(function(error) {
            console.log(error);
        });
}

add_game = function(name, source, nowplayed) {
    axios.put('/game', {
            user: app.username,
            game_name: name,
            source_name: source,
            nowplayed: nowplayed
        })
        .then(function(response) {
            console.log(response);
            if (response.data.error) {
                app.$bvToast.toast(message = 'Error Adding ' + name + ': ' + response.data.error,
                    options = {
                        title: 'Error',
                        autoHideDelay: 5000
                    });
                return;
            }
            app.$bvToast.toast(message = 'Successfully Added ' + name + ' as gameid ' + response.data.gameid,
                options = {
                    title: 'Success',
                    autoHideDelay: 5000
                });
        })
        .catch(function(error) {
            console.log(error);
            app.$bvToast.toast(message = 'Error Adding ' + name + ': ' + error,
                options = {
                    title: 'Error',
                    autoHideDelay: 5000
                });
        });
}

game_submit = function(game, message, data) {
    app.$bvModal.hide('edit_game_other');
    var params = {
        user: app.username,
        gameid: game.gameid,
        finished: null,
        playtime: null,
        rawdata: null
    };
    if(message=="finished"){
        params['finished'] = 1;
    } else if(message=="unfinished"){
        params['finished'] = 0;
    } else if(message=="playtime"){
        params['playtime'] = data;
    } else if(message=="rawdata"){
        params['rawdata'] = data;
    }
    axios.patch('/game', params)
        .then(function(response) {
            console.log(response);
            if (response.data.error) {
                app.$bvToast.toast(message = 'Error updating ' + game.name + ': ' + response.data.error,
                    options = {
                        title: 'Error',
                        autoHideDelay: 5000
                    });
                return;
            }
            app.$bvToast.toast(message = 'Successfully updated ' + game.name + ' as gameid ' + response.data.gameid+' '+JSON.stringify(response.data.diff),
                options = {
                    title: 'Success',
                    autoHideDelay: 5000
                });
            app.get_game_page(true);
        })
        .catch(function(error) {
            console.log(error);
            app.$bvToast.toast(message = 'Error updating ' + game.name + ': ' + error,
                options = {
                    title: 'Error',
                    autoHideDelay: 5000
                });
        });
}

game_delete = function(game) {
    app.$bvModal.hide('edit_game_other');
    var params = {
        user: app.username,
        gameid: game.gameid,
    };
    axios.delete('/game', {data: params})
        .then(function(response) {
            console.log(response);
            if (response.data.error) {
                app.$bvToast.toast(message = 'Error deleting ' + game.name + ': ' + response.data.error,
                    options = {
                        title: 'Error',
                        autoHideDelay: 5000
                    });
                return;
            }
            app.$bvToast.toast(message = 'Successfully deleted ' + game.name,
                options = {
                    title: 'Success',
                    autoHideDelay: 5000
                });
            app.get_game_page(true);
        })
        .catch(function(error) {
            console.log(error);
            app.$bvToast.toast(message = 'Error deleting ' + game.name + ': ' + error,
                options = {
                    title: 'Error',
                    autoHideDelay: 5000
                });
        });
}

games_method = function(game, method) {
    var params = {
        user: app.username,
        gameid: game.gameid,
        method: method
    };
    axios.patch('/games_method', params)
        .then(function(response) {
            console.log(response);
            if (response.data.error) {
                app.$bvToast.toast(message = 'Error on method ' + method + ' for ' + game.name + ': ' + response.data.error,
                    options = {
                        title: 'Error',
                        autoHideDelay: 5000
                    });
                return;
            }
            app.$bvToast.toast(message = 'Successfully '+method+' on ' + game.name + ' as gameid ' + response.data.gameid,
                options = {
                    title: 'Success',
                    autoHideDelay: 5000
                });
            app.get_game_page(true);
        })
        .catch(function(error) {
            console.log(error);
            app.$bvToast.toast(message = 'Error updating ' + game.name + ': ' + error,
                options = {
                    title: 'Error',
                    autoHideDelay: 5000
                });
        });
}

update_screenshots = function(source) {
    var params = {
        user: app.username,
        method: 'screenshots',
        source: source
    };
    axios.patch('/update_method', params)
        .then(function(response) {
            console.log(response);
            if (response.data.error) {
                app.$bvToast.toast(message = 'Error updating screenshots.' + response.data.error,
                    options = {
                        title: 'Error',
                        autoHideDelay: 5000
                    });
                return;
            }
            app.$bvToast.toast(message = 'Successfully started job update screenshots',
                options = {
                    title: 'Success',
                    autoHideDelay: 5000
                });
            app.get_game_page(true);
        })
        .catch(function(error) {
            console.log(error);
            app.$bvToast.toast(message = 'Error updating screenshots',
                options = {
                    title: 'Error',
                    autoHideDelay: 5000
                });
        });
}

if (app.username) {
    load_sources();
    load_games(0, app.perPage);
}