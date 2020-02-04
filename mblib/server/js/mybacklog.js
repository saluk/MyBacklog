function pad(num) {
    var s = "00" + num;
    return s.substr(s.length-2);
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
            text: 'Filter by finished'
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
        nice_time: function(game) {
            return playtime_to_hour_min_sec(game.playtime);
        },
        nice_date: function(game) {
            if(!game.lastplayed) {
                return 'never'
            }
            var dt = moment.utc(game.lastplayed,'H:m:s YYYY-M-D');
            return dt.fromNow();
            return {
                'date': dt.format('MM/DD/YYYY'),
                'time': dt.format('hh:mm a')
            }
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
            add_game(this.add_name, this.add_source);
            //this.add_name = '';
            //this.add_source = '';
        },
        set_time_modal(game) {
            this.edit_game = game;
            this.$bvModal.show('edit_game_playtime');
        },
        set_lastplayed_modal(game) {
            this.edit_game = game;
            this.$bvModal.show('edit_game_lastplayed');
        },
        playing_modal(game) {
            games_method(game, 'start_playing_game');
            this.edit_game = game;
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
            game_submit(this.edit_game, "rawdata", this.edit_game);
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
                text: 'filter by source',
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

add_game = function(name, source) {
    axios.put('/game', {
            user: app.username,
            game_name: name,
            source_name: source
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
    var params = {
        user: app.username,
        gameid: game.gameid,
        finished: null,
        playtime: null,
        rawdata: null
    };
    if(message=="finished"){
        params['finished'] = 1;
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
                app.$bvToast.toast(message = 'Error on method ' + method + ' for ',game.name + ': ' + response.data.error,
                    options = {
                        title: 'Error',
                        autoHideDelay: 5000
                    });
                return;
            }
            app.$bvToast.toast(message = 'Successfully operation on ' + game.name + ' as gameid ' + response.data.gameid,
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

if (app.username) {
    load_sources();
    load_games(0, app.perPage);
}