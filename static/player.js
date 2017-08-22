String.prototype.toMMSS = function () {
    var seconds = parseInt(this);
    var minutes = Math.floor(seconds / 60);
    seconds -= minutes*60;

    if (minutes < 10) {minutes = "0"+minutes;}
    if (seconds < 10) {seconds = "0"+seconds;}
    return minutes+':'+seconds;
};

$(function () {
    var playlistCard, playerData = null, statusInterval, seekSlider, seekInterval, ignoreSeek = false;

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

    var reloadpage = function (data) {
        $('body').load(' #mainDiv', onreloadpage);
    };

    var updateSeekSlider = function(slider){
        slider = slider || seekSlider
        slider.next().text(slider.val().toMMSS()+'/'+slider.attr('max').toMMSS());        
    };

    onreloadpage = function () {
        playlistCard = $("#content > div:nth-child(2)");
        seekSlider = $('input#seekControl');

        playlistf();

        $('input#volumeControl').on('input', function () {
            $.ajax('vol/' + $(this).val());
            $(this).next().text(Math.round($(this).val()*100)+'%');
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
        $('input#duckVolumeControl').on('input', formf('opt', null, function(element){
            $(element).next().text(Math.round($(element).val()*100)+'%');            
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
        
        $('[type="range"]~span').each(function(){
            if($(this).data('isseek') == undefined){
                $(this).text(Math.round($(this).prev().val()*100)+'%');
            } else {
                $(this).text($(this).prev().val().toMMSS()+'/'+$(this).prev().attr('max').toMMSS());                
            }
        });
    };

    onreloadpage();

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
                if (playerData.paused != ddata.paused || playerData.queue != ddata.queue || playerData.items != ddata.items ||
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
        if (seekSlider && playerData && !playerData.paused) {
            seekSlider.val(parseInt(seekSlider.val()) + 1);
            updateSeekSlider();
        }
    }, 1000);
});
