$(function () {
    var playlistCard, vc;

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
            return after(this);
        }
    };

    var reloadpage = function (data) {
        $('body').load(' #mainDiv', onreloadpage);
    };

    onreloadpage = function () {
        playlistCard = $("#content > div.card");
        vc = $('input#volumeControl');

        playlistf();

        vc.on('input', function () {
            $.ajax('vol/' + vc.val());
        });

        $('form#add').on('submit', formf('add', reloadpage, function(element){
            $('#add > div > div.modal-footer > button.btn.btn-primary').attr('disabled', true);
            return false;
        }));

        $('form#opt > div.btn-group').on('change', formf('opt'));
        $('input#duckVolumeControl').on('input', formf('opt'));

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
    };

    onreloadpage();

    $(document).ajaxError(function (event, jqxhr, settings, thrownError) {
        console.error('url: ' + settings.url + '\nErro: ' + thrownError);
        reloadpage();
    });
});
