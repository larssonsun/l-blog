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

$(document).ready(function(){
    //caotm的我不知道如何在markdown生成的toc里面注入class和属性，只能自己用脚本注册
    
    //uk-scrollspy-nav="closest: li; scroll: true; offset: 100"
    $(".l-sidebar-right > div > div > ul").attr("uk-scrollspy-nav", "closest: li; scroll: true; offset: 80");

    //uk-nav uk-nav-default tm-nav uk-nav-parent-icon
    $(".l-sidebar-right > div > div ul").addClass("uk-nav uk-nav-default l-nav uk-nav-parent-icon")
    
});