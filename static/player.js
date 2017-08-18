$(function () {
    var playlistCard = $("#content > div.card");
    var vc = $('input#volumeControl');

    var playlistF = function () {
        playlistCard.outerHeight($(window).height() - playlistCard.offset().top - 2);
    };

    var optF = function () {
        $.ajax({
            url: 'opt',
            type: 'post',
            data: $('form#opt').serialize()
        });
    };

    playlistF();

    vc.on('input', function () {
        $.ajax('vol/' + vc.val());
    });

    $('form#opt > div.btn-group').on('change', optF);

    $('input#duckVolumeControl').on('input', optF);

    $('.alert').on('closed.bs.alert', playlistF);

    $('[data-toggle="list"]').on('shown.bs.tab', playlistF);

    $(window).on('resize', playlistF);
});