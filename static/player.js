String.prototype.toMMSS = function () {
    var seconds = parseInt(this);
    var minutes = Math.floor(seconds / 60);
    seconds -= minutes * 60;

    if (minutes < 10) { minutes = "0" + minutes; }
    if (seconds < 10) { seconds = "0" + seconds; }
    return minutes + ':' + seconds;
};

$(function () {
    var playlistCard, playerData = null, statusInterval, seekSlider, seekInterval, ignoreSeek = false,
        eventListener;

    var playlistf = function () {
        playlistCard.outerHeight($(window).height() - playlistCard.offset().top - 2);
    };

    var formf = function (formId, success, after) {
        return function () {
            $.ajax({
                url: formId,
                type: 'post',
                data: $('form#' + formId).serialize(),
                success: success
            });
            if (after) return after(this);
        }
    };

    var eventf = function (func) {
        return function (event) {
            if (event.originalEvent.data) {
                data = JSON.parse(event.originalEvent.data)
                func(data);
            }
        }
    }

    var reloadpage = function (data) {
        $('body').load(' #mainDiv', onreloadpage);
    };

    var updateSeekSlider = function (slider) {
        slider = slider || seekSlider
        slider.next().text(slider.val().toMMSS() + '/' + slider.attr('max').toMMSS());
    };

    onreloadpage = function () {
        playlistCard = $("#content > div:nth-child(2)");
        seekSlider = $('input#seekControl');

        playlistf();

        $('input#volumeControl').on('input', function () {
            $.ajax('vol/' + $(this).val());
            $(this).next().text(Math.round($(this).val() * 100) + '%');
        });

        seekSlider.on('input', function () {
            $.ajax('seek/' + $(this).val());
            ignoreSeek = true;
            updateSeekSlider();
        });

        $('form#add').on('submit', formf('add', reloadpage, function () {
            $('#add > div > div.modal-footer > button.btn.btn-primary').attr('disabled', true);
            return false;
        }));

        $('form#opt > div.btn-group').on('change', formf('opt'));
        $('input#duckVolumeControl').on('input', formf('opt', null, function (element) {
            $(element).next().text(Math.round($(element).val() * 100) + '%');
        }));

        $('.alert').on('closed.bs.alert', playlistf);
        $('[data-toggle="list"]').on('shown.bs.tab', playlistf);
        $(window).on('resize', playlistf);

        $('[data-ajaxurl]').on('click', function () {
            $.ajax({
                url: $(this).data('ajaxurl'),
                success: reloadpage
            });
            return false;
        });

        $('[type="range"]~span').each(function () {
            if ($(this).data('isseek') == undefined) {
                $(this).text(Math.round($(this).prev().val() * 100) + '%');
            } else {
                $(this).text($(this).prev().val().toMMSS() + '/' + $(this).prev().attr('max').toMMSS());
            }
        });

        $('#closeBtn').on('click', function () {
            return confirm('Desconectar o player?');
        });
    };

    onreloadpage();

    eventListener = new EventSource('events/');

    eventListener.onmessage = function (event) {
        console.debug(event);
    };

    $(eventListener).on('handshake', eventf(function (data) {
        playerData = data;
    })).on('firstframe', eventf(function (data) {
        seekSlider.val(0);
        updateSeekSlider();
    })).on('volumeupdate', eventf(function (data) {
        if (data.vol) {
            $('#volumeControl').val(parseFloat(data.vol)).next().text(Math.round(data.vol * 100) + '%');

        } else if (data.dvol) {
            $('#duckVolumeControl').val(parseFloat(data.dvol)).next().text(Math.round(data.dvol * 100) + '%');
        }
    })).on('playlistadd', eventf(function (data) {
        idx = $('#tableList').children().length
        $('<tr>\
        <th class="text-center" scope="row">'+ (idx + 1) + '</th>\
        <td class="text-center"><a href="#" data-ajaxurl="play/'+ idx + '">▶️</a></td>\
        <td class="text-center"><a href="#" data-ajaxurl="remove/'+ idx + '">❌</a></td>\
        <td class="text-center">'+ (data.duration + '').toMMSS() + '</td>\
        <td><a href="'+ data.webpage_url + '">' + data.title + '</a></td>\
        </tr>').appendTo('#tableList').on('click', '[data-ajaxurl]', function () {
            $.ajax({
                url: $(this).data('ajaxurl'),
                success: reloadpage
            });
            return false;
        });
        $('#playlistHeader').text('Playlist '+(idx+1)+'/'+(playerData.queue+playerData.items)+(playerData.items ? ' 🔄' : ''));
    }));

    $(document).ajaxError(function (event, jqxhr, settings, thrownError) {
        console.error('url: ' + settings.url + '\nStatus: ' + jqxhr.status + '\nErro: ' + (thrownError || jqxhr.statusText));
        if (!(jqxhr.status == 0 || jqxhr.status == 404)) reloadpage();
        else {
            clearInterval(seekInterval)
            clearInterval(statusInterval);
        }
    });

    statusInterval = setInterval(function () {
        $.ajax({
            url: 'status',
            success: function (data) {
                ddata = data.data
                playerData = playerData || ddata
                count = $('#tableList').children().length
                if (playerData.paused != ddata.paused || count != ddata.queue ||
                    (playerData.curItem == null && ddata.curItem) || (playerData.curItem && ddata.curItem == null)) {
                    reloadpage();
                } else if (playerData.curItem && ddata.curItem) {
                    if (playerData.curItem.id != ddata.curItem.id) {
                        reloadpage();
                    } else if(ignoreSeek){
                        ignoreSeek = false;
                    } else if (seekSlider && ddata.curItem.frame) {
                        seekSlider.val(Math.round(ddata.curItem.frame / ddata.curItem.fps));
                        updateSeekSlider();
                    }
                }
                playerData = ddata
            }
        });
    }, 5000);

    seekInterval = setInterval(function () {
        if (seekSlider && playerData && playerData.curItem && !playerData.paused) {
            seekSlider.val(parseInt(seekSlider.val()) + 1);
            updateSeekSlider();
        }
    }, 1000);
});
