/**
 * created by larsson on 8.10 2018
 * data storage in html elements was not comfort HTML5 standard
 */

$(document).ready(function () {

    

    //caotm的我不知道如何在markdown生成的toc里面注入class和属性，只能自己用脚本注册
    //uk-scrollspy-nav="closest: li; scroll: true; offset: 100"
    $(".l-sidebar-right > div > div > ul").attr("uk-scrollspy-nav", "closest: li; scroll: true; offset: 80");
    //uk-nav uk-nav-default tm-nav uk-nav-parent-icon
    $(".l-sidebar-right > div > div ul").addClass("uk-nav uk-nav-default l-nav uk-nav-parent-icon")

    var ajxJson = function (url, method, data, successFunc, errFunc) {
        $.ajax({
            type: method,
            url: url,
            data: data,
            dataType: 'json',
            success: successFunc,
            error: errFunc
        });
    }

    var persec = function (jqObj, orgTxt, s, callback){
        jqObj.empty().append(orgTxt + "(" + s + ")");
        s=s-1;
        if(s>=0){
            setTimeout(function(){
                persec(jqObj, orgTxt, s, callback);
            },1000);
        }
        else {
            jqObj.text(orgTxt);
            if(callback)
                callback();
        }
    }

    //----------------评论----------------

    var showMsg = function (msg, status, callbackFn) {

        var iconStr = status == "danger" ? "<span uk-icon='icon: warning'></span> " :
            status == "success" ? "<span uk-icon='icon: check'></span> " : "";
        UIkit.notification({
            message: iconStr + msg,
            status: status,
            pos: "top-center",
            timeout: 4000
        });
        if (callbackFn) {
            UIkit.util.on(document, "close", ".uk-notification", callbackFn);
        }
        $(".uk-notification-message").removeClass("l-notification").addClass("l-notification");
    }

    var showCmmForBlog = function () {
        $("#artclAndCmmDiv2").append($("#sendCommentFrm"));
        $("#sendCommentFrm").removeClass("l-form-Cmm");
        $(".l-form-Cmm-BlogCancel").click(null);

        $("#sendCommentBttn").removeAttr("data-ForCommId");
        $("#sendCommentBttn").removeAttr("data-to-cmm-username");
        $("#sendCommentBttn").removeAttr("data-isLevelCmm");

        if ($(this).text() == "回复") {
            $("#sendCommentTa").val("");
            $("#sendCommentTa").focus();
        }
        return true;
    }

    var showCmmForCmm = function () {
        var atclH = $(this).parents("article")[0];
        $("#sendCommentFrm").addClass("l-form-Cmm");
        $(atclH).append($("#sendCommentFrm"));
        $(".l-form-Cmm-BlogCancel").click(showCmmForBlog);

        $("#sendCommentBttn").removeAttr("data-ForCommId");
        $("#sendCommentBttn").removeAttr("data-to-cmm-username");
        $("#sendCommentBttn").removeAttr("data-isLevelCmm");
        $("#sendCommentBttn").attr("data-ForCommId", $(this).attr("data-ForCommId"));
        $("#sendCommentBttn").attr("data-to-cmm-username", $(this).attr("data-to-cmm-username"));
        $("#sendCommentBttn").attr("data-isLevelCmm", $(this).attr("data-isLevelCmm"));

        $("#sendCommentTa").val("");
        $("#sendCommentTa").focus();
        return false;
    }

    //准备回复主贴
    $("#goSndCommFrAtcl").click(showCmmForBlog);

    //准备回复主回贴
    $(".l-comment-button").not(".l-comment-button-chd").click(showCmmForCmm);

    //准备回复次回贴
    $(".l-comment-button-chd").click(showCmmForCmm);

    //提交回复
    $("#sendCommentBttn").click(function () {

        //validate commit interval
        t = sessionStorage.getItem("lastCommitTime")
        if(t){
            var diffT = Date.parse(new Date()) - t;
            if (diffT < 30000) {
                showMsg("两次评论间隔过短，请" + (30 - parseInt(diffT / 1000)) + "s 后再试", "warning");
                return;
            }
        }

        var URL = $(this).attr('url-send-cmm');
        var forCmmId = $(this).attr("data-ForCommId");
        var toCmmUserName = $(this).attr("data-to-cmm-username");
        var isLv2Cm = $(this).attr("data-isLevelCmm");
        var blogId = $(this).attr("data-blog-id");
        var blogUserName = $(this).attr("data-blog-username");
        var content = $("#sendCommentTa").val();

        //validate posted content
        if (content.length < 5) {
            showMsg("请输入至少5个字符", "warning");
            return;
        }

        //暂时禁止鼠标滚动，防止偏移
        // $(document).bind('mousewheel', function(event, delta) { return false; });
        // $(document).bind('mousedown', function(event, delta) { return false; });

        //post to serv
        $.ajax({
            type: 'post',
            url: URL,
            data: {
                'blog_Id': blogId,
                'blog_username': blogUserName,
                'content': content,
                'parent_comment_id': forCmmId,
                'to_comm_username': toCmmUserName,
                'isLv2Cm': isLv2Cm
            },
            dataType: 'json',
            success: function (result) {
                if (new Number(result.error_code) < 0) {
                    var newCmmLi = $($("UL.l-comment-list > LI:first"));
                    topDeff = 85;
                    if (forCmmId) {
                        bttn = $("#sendCommentFrm");
                        li = bttn.parents("li")[0];
                        ul = $(li).find(".l-commentForCmm-list")[0];
                        artical = $(ul).find("article:last");
                        newCmmLi = $(artical);
                        topDeff = 135;
                    }

                    sessionStorage.setItem("lastCommitTime", Date.parse(new Date()))
                    window.location.reload();
                    $("html,body").animate({ scrollTop: newCmmLi.offset().top - topDeff }, 0);
                }
                else {
                    if ("30001" == result.error_code)
                        showMsg(result.error_msg, "warning")
                    else {
                        showMsg(result.error_msg, "danger")
                    }
                }
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                showMsg(textStatus, "danger")
            }
        });
    });

    //----------------登录----------------

    UIkit.util.on($('#loginModel'), 'shown', function () {
        $('#loginModel').find("input")[0].focus();
    });

    UIkit.util.on($('#loginModel'), 'hidden', function () {
        var approve = $('#approve');
        var recover = $('#recover');
        approve.attr("hidden", true);
        approve.find("input[class='uk-input']").each(function(){
            $(this).val("");
        });
        recover.attr("hidden", true);
        recover.find("input[class='uk-input']").each(function(){
            $(this).val("");
        });
    });

    var validate_login = function (usernameCtl, pwdCtl, msgCtl) {
        return true;
    }
    
    $("#loginModel").keypress(function(e) {
        //Enter key
        if (e.which == 13) {
            return false;
        }
    });

    //登录按钮
    $("#lognBttn").click(function() {

        var submitBttn = $(this);
        var form = $(submitBttn.parents("form"));
        var URL = submitBttn.attr("url-send-login");
        var usernameCtl = $(form.find("input[name='userName']")[0]);
        var pwdCtl = $(form.find("input[name='pwd']")[0]);
        var loginMsg = $("#loginMsg");
        var spin = $($("#loginModel").find(".l-spinner")[0]);

        if (!validate_login(usernameCtl, pwdCtl, loginMsg)) {
            return;
        }

        spin.removeClass("l-spinner");
        submitBttn.attr("disabled", "");

        ajxJson(URL, "post", { "username": usernameCtl.val(), "pwd": pwdCtl.val() },
            function (result) {
                if (new Number(result.error_code) < 0) {
                    window.location.reload();
                }
                else
                    loginMsg.text(result.error_msg);

                spin.addClass("l-spinner");
                submitBttn.removeAttr("disabled");
            },
            function (XMLHttpRequest, textStatus, errorThrown) {
                loginMsg.text(textStatus);
                spin.addClass("l-spinner");
                submitBttn.removeAttr("disabled");
            });

    });

    //----------------注册----------------

    UIkit.util.on($('#registeModel'), 'shown', function () {
        $('#registeModel').find("input")[0].focus();
    });

    $("#registeModel").keypress(function(e) {
        //Enter key
        if (e.which == 13) {
            return false;
        }
    });

    var validate_regist = function (emailCtl, usernameCtl, pwdCtl, repwdCtl, msgCtl) {
        return true;
    }

    $("#registeBttn").click(function () {

        var submitBttn = $(this);
        var form = $(submitBttn.parents("form.reg-form"));
        var URL = submitBttn.attr("url-send-regist");

        var emailCtl = $(form.find("input[name='reg-email']")[0]);
        var usernameCtl = $(form.find("input[name='reg-username']")[0]);
        var pwdCtl = $(form.find("input[name='reg-pwd']")[0]);
        var repwdCtl = $(form.find("input[name='reg-repwd']")[0]);
        var registMsg = $("#registMsg");

        var spin = $($("#registModel").find(".l-spinner")[0]);

        if (!validate_regist(emailCtl, usernameCtl, pwdCtl, repwdCtl, registMsg)) {
            return;
        }

        spin.removeClass("l-spinner");
        submitBttn.attr("disabled", "");

        ajxJson(URL, "post", {
            "email": emailCtl.val(),
            "username": usernameCtl.val(),
            "pwd": pwdCtl.val(),
            "repwd":repwdCtl.val()
        },
            function (result) {
                if (new Number(result.error_code) < 0) {
                    // window.location.reload();
                    showMsg(result.error_msg, "success")
                    //clear page
                    emailCtl.val("");
                    usernameCtl.val("");
                    pwdCtl.val("");
                    repwdCtl.val("");
                    registMsg.text("");
                    submitBttn.removeAttr("disabled");
                    //close
                    UIkit.modal($("#registeModel")).hide();
                }
                else if(new Number(result.error_code) == 10008) {
                    registMsg.text(result.error_msg);
                    waits = result.data["waits"];
                    persec(submitBttn, submitBttn.text(), waits, function(){
                        registMsg.text("");
                        submitBttn.removeAttr("disabled");
                    });
                }
                else {
                    registMsg.text(result.error_msg);
                    submitBttn.removeAttr("disabled");
                }

                spin.addClass("l-spinner");
            },
            function (XMLHttpRequest, textStatus, errorThrown) {
                registMsg.text(textStatus);
                spin.addClass("l-spinner");
                submitBttn.removeAttr("disabled");
            });
    });

    //----------------激活----------------

    var validate_approve = function (usernameCtl) {
        return true;
    }

    $("#approveBttn").click(function() {

        var approveBttn = $(this);
        var form = $(approveBttn.parents("form"));
        var URL = approveBttn.attr("url-send-approve");
        var usernameCtl = $(form.find("input[name='userName']")[0]);
        var loginMsg = $("#loginMsg");
        // var spin = $($("#loginModel").find(".l-spinner")[0]);

        if (!validate_approve(usernameCtl)) {
            return;
        }

        // spin.removeClass("l-spinner");
        approveBttn.attr("disabled", "");

        ajxJson(URL, "post", { "username": usernameCtl.val() },
            function (result) {
                if (new Number(result.error_code) < 0) {
                    window.location.reload();
                }
                else
                    loginMsg.text(result.error_msg);

                // spin.addClass("l-spinner");
                approveBttn.removeAttr("disabled");
            },
            function (XMLHttpRequest, textStatus, errorThrown) {
                loginMsg.text(textStatus);
                // spin.addClass("l-spinner");
                approveBttn.removeAttr("disabled");
            });

    });

});