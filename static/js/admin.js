/**
 * created by larsson on 9.21 2018
 * js for admin pad
 */
$(document).ready(function () {

    var adminPad = $("#adminPad");
    var resetIndex = adminPad.find("a[name='reset-index']")[0];
    var redo = true;

    $(resetIndex).click(function () {
        
        var resetIndexBttn = $(this);
        var URL = resetIndexBttn.attr("url-send-resetindex")
        // resetIndexBttn.attr("disabled", "");
        
        if(redo) {
            redo = false;
            ajxJson(URL, "post", null,
                function (result) {
                    if (new Number(result.error_code) < 0) {
                        showMsg(result.error_msg, "success")
                    }
                    else
                        showMsg(result.error_msg, "warning")
                    redo = true;
                    // resetIndexBttn.removeAttr("disabled");
                },
                function (XMLHttpRequest, textStatus, errorThrown) {
                    showMsg(textStatus, "danger")
                    redo = true;
                    // resetIndexBttn.removeAttr("disabled");
                });
            }
        return false;
    });
});