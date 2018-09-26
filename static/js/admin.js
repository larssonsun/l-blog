/**
 * created by larsson on 9.21 2018
 * js for admin pad
 */

$(document).ready(function () {

    var redo = true;
    var adminPad = $(".adminPad");
    
    //resetindex
    var resetIndex = adminPad.find("a[name='reset-index']");
    
    $(resetIndex).click(function () {
        
        var resetIndexBttn = $(this);
        var URL = resetIndexBttn.attr("url-send-resetindex")
        if (redo) {
            redo = false;
            ajxJson(URL, "post", null,
                function (result) {
                    if (new Number(result.error_code) < 0) {
                        showMsg(result.error_msg, "success")
                    }
                    else
                        showMsg(result.error_msg, "warning")
                    redo = true;
                },
                function (XMLHttpRequest, textStatus, errorThrown) {
                    showMsg(textStatus, "danger")
                    redo = true;
                });
        }
        redo = true;
        return false;
    });

    //resetblogcache
    var resetRss = adminPad.find("a[name='reset-blog-cache']");
    $(resetRss).click(function () {

        var restBlogCacheBttn = $(this);
        var URL = restBlogCacheBttn.attr("url-send-resetblogcache")
        if (redo) {
            redo = false;
            ajxJson(URL, "post", null,
                function (result) {
                    if (new Number(result.error_code) < 0) {
                        showMsg(result.error_msg, "success")
                    }
                    else
                        showMsg(result.error_msg, "warning")
                    redo = true;
                },
                function (XMLHttpRequest, textStatus, errorThrown) {
                    showMsg(textStatus, "danger")
                    redo = true;
                });
        }
        redo = true;
        return false;
    });

    //reset rss
    var resetRss = adminPad.find("a[name='reset-rss']");
    $(resetRss).click(function () {

        var resetRssBttn = $(this);
        var URL = resetRssBttn.attr("url-send-resetrss")
        if (redo) {
            redo = false;
            ajxJson(URL, "post", null,
                function (result) {
                    if (new Number(result.error_code) < 0) {
                        showMsg(result.error_msg, "success")
                    }
                    else
                        showMsg(result.error_msg, "warning")
                    redo = true;
                },
                function (XMLHttpRequest, textStatus, errorThrown) {
                    showMsg(textStatus, "danger")
                    redo = true;
                });
        }
        redo = true;
        return false;
    });
});