/**
 * created by larsson on 9.28 2018
 * data storage in html elements was not comfort HTML5 standard
 */

$(document).ready(function(){

    //copy code to clipboard
    $(".codehilite > pre").prepend("<span class='copy-code uk-text-right' uk-icon='icon: copy; ratio: 0.7'></span><br>")
    $('.copy-code').on('click', function () {
        var code = $(this).parent().text();
        var ta = document.createElement('textarea');
        ta.value = code;
        ta.setAttribute('readonly', '');
        ta.style.position = 'absolute';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        const selected = document.getSelection().rangeCount > 0 ?
            document.getSelection().getRangeAt(0) : false;
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        if (selected) {
            document.getSelection().removeAllRanges();
            document.getSelection().addRange(selected);
        }
        return false;
    });
});
