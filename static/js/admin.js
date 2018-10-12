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

    //reset robots
    var resetRobots = adminPad.find("a[name='reset-robots']");
    $(resetRobots).click(function () {

        var resetRobotsBttn = $(this);
        var URL = resetRobotsBttn.attr("url-send-resetrobots")
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

    //setblogdetail
    $("#setblogdetailBttn").click(function () {

        $(this).attr("disabled", "");

        var URL = $(this).attr("url-send-blogtmp");
        var frm = $("#setblogdetail");
        var blogid = frm.find("[name='blogid']")[0];
        var source_from = frm.find("[name='source_from']");
        source_from = source_from[0].checked ? "original" : "transfer";
        var name = frm.find("[name='name']")[0];
        var name_en = frm.find("[name='name_en']")[0];
        var title_image_filename = frm.find("[name='title_image_filename']")[0];
        var title_image_bgcolor = frm.find("[name='title_image_bgcolor']")[0];
        var summary = frm.find("[name='summary']")[0];
        var content = frm.find("[name='content']")[0];

        var catelog = "";
        var catelogCtl = frm.find("ul[name='catelog']")[0];
        var cbs = $(catelogCtl).find("input[type='radio']")
        for (var i = 0; i < cbs.length; i++) {
            if (cbs[i].checked)
                catelog += $(cbs[i]).attr("catename") + ",";
        }
        if (cbs.length > 0)
            catelog = catelog.substring(0, catelog.length - 1);

        var tags = "";
        var tagsCtl = frm.find("ul[name='tags']")[0];
        cbs = $(tagsCtl).find("input[type='checkbox']");
        for (var i = 0; i < cbs.length; i++) {
            if (cbs[i].checked)
                tags += $(cbs[i]).attr("tagname") + ",";
        }
        if (cbs.length > 0)
            tags = tags.substring(0, tags.length - 1);

        var shit = {
            "blogid": $(blogid).val(),
            "source_from": source_from,
            "name": $(name).val(),
            "name_en": $(name_en).val(),
            "title_image_filename": $(title_image_filename).val(),
            "title_image_bgcolor": $(title_image_bgcolor).val(),
            "summary": $(summary).val(),
            "content": $(content).val(),
            "catelog": catelog,
            "tags": tags
        }

        ajxJson(URL, "post", shit, function (result) {
            if (new Number(result.error_code) < 0) {
                // window.location.reload();
                showMsg(result.error_msg, "success")
            }
            else {
                showMsg(result.error_msg, "danger")
            }
        },
            function (XMLHttpRequest, textStatus, errorThrown) {
                showMsg(textStatus, "danger")
            });

        $(this).removeAttr("disabled");
    });

    //deleteblog
    $("#deleteblogBttn").click(function () {
        var bttn = $(this);
        UIkit.modal.confirm('UIkit confirm!').then(function () {
            bttn.attr("disabled", "");

            var URL = bttn.attr("url-send-deleteblog");
            var id = bttn.attr("data-blog-id");
            ajxJson(URL, "post", { "id": id }, function (result) {
                if (new Number(result.error_code) < 0) {
                    // window.location.reload();
                    showMsg(result.error_msg, "success")
                }
                else {
                    showMsg(result.error_msg, "danger")
                }
            },
            function (XMLHttpRequest, textStatus, errorThrown) {
                showMsg(textStatus, "danger")
            });

            bttn.removeAttr("disabled");
        }, function () { });

        return false;
    });

    //loadlastcache
    $("#loadlastcacheBttn").click(function () {
        $(this).attr("disabled", "");

        var URL = $(this).attr("url-send-loadlastcache");
        ajxJson(URL, "post", null, function (result) {
            if (new Number(result.error_code) < 0) {
                blog = result.data;
                if (!blog)
                    showMsg(result.error_msg, "danger");
                else {
                    var frm = $("#setblogdetail");
                    var blogid = frm.find("[name='blogid']")[0];
                    var source_from = frm.find("[name='source_from']");
                    var name = frm.find("[name='name']")[0];
                    var name_en = frm.find("[name='name_en']")[0];
                    var title_image_filename = frm.find("[name='title_image_filename']")[0];
                    var title_image_bgcolor = frm.find("[name='title_image_bgcolor']")[0];
                    var summary = frm.find("[name='summary']")[0];
                    var content = frm.find("[name='content']")[0];
                    var catelogCtl = frm.find("ul[name='catelog']")[0];
                    var tagsCtl = frm.find("ul[name='tags']")[0];

                    $(blogid).val(blog.blogid);
                    $(name).val(blog.name);
                    $(name_en).val(blog.name_en);
                    source_from[0].checked = blog.source_from == "original" ? true : false;
                    source_from[1].checked = blog.source_from == "transfer" ? true : false;
                    $(title_image_filename).val(blog.title_image_filename);
                    $(title_image_bgcolor).val(blog.title_image_bgcolor);
                    $(summary).val(blog.summary);
                    $(content).val(blog.content);
                    var cbs = $(catelogCtl).find("input[type='radio']");
                    $.each(blog.catelog, function (i, cate) {
                        var cb = $(cbs).filter("[catename='" + cate + "']");
                        if (cb)
                            $(cb).prop("checked", true);
                    });

                    cbs = $(tagsCtl).find("input[type='checkbox']");
                    $.each(blog.tags, function (i, tag) {
                        var cb = $(cbs).filter("[tagname='" + tag + "']");
                        if (cb)
                            $(cb).prop("checked", true);
                    });

                    showMsg(result.error_msg, "success")
                }
            }
            else {
                showMsg(result.error_msg, "danger")
            }
        },
            function (XMLHttpRequest, textStatus, errorThrown) {
                showMsg(textStatus, "danger")
            });

        $(this).removeAttr("disabled");

        return false;
    });

    //publicblogdetail
    $("#publicblogdetailBttn").click(function () {

        $(this).attr("disabled", "");

        var URL = $(this).attr("url-send-publicblog");
        ajxJson(URL, "post", {}, function (result) {
            if (new Number(result.error_code) < 0) {
                // window.location.reload();
                showMsg(result.error_msg, "success")
            }
            else {
                showMsg(result.error_msg, "danger")
            }
        },
            function (XMLHttpRequest, textStatus, errorThrown) {
                showMsg(textStatus, "danger")
            });

        $(this).removeAttr("disabled");
    });
});