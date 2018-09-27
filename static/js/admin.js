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
    var resetBlogcache = adminPad.find("a[name='reset-blog-cache']");
    $(resetBlogcache).click(function () {

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

    //reset feeds
    var resetFeeds = adminPad.find("a[name='reset-feeds']");
    $(resetFeeds).click(function () {

        var resetFeedsBttn = $(this);
        var URL = resetFeedsBttn.attr("url-send-resetfeeds")
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

    //reset sitemap
    var resetSitemap = adminPad.find("a[name='reset-sitemap']");
    $(resetSitemap).click(function () {

        var resetSitemapBttn = $(this);
        var URL = resetSitemapBttn.attr("url-send-resetsitemap")
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