$(function () {

    var vc = $('input#volumeControl');
    vc.on('input', function () {
        $.ajax('vol/' + vc.val());
    });

    var optF = function () {
        $.ajax({
            url: 'opt',
            type: 'post',
            data: $('form#opt').serialize()
        });
    }

    $('form#opt > div.btn-group').on('change', optF);

    $('input#duckVolumeControl').on('input', optF);
});