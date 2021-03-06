/**
 * created by larsson on 9.28 2018
 * data storage in html elements was not comfort HTML5 standard
 */

$(document).ready(function(){

    //copy code to clipboard
    $(".codehilite > pre").prepend("<a href='' class='copy-code' uk-icon='icon: copy; ratio: 0.7'></a><br>")
    $('.copy-code').on('click', function () {
        var code = $(this).parent().text();
        var ta = document.createElement('textarea');
        ta.value = code;
        ta.setAttribute('readonly', '');
        ta.style.position = 'absolute';
        ta.style.left = '-9999px';
        
        try{
            //document.body.appendChild(ta);
            this.appendChild(ta);
            const selected = document.getSelection().rangeCount > 0 ?
            document.getSelection().getRangeAt(0) : false;
            ta.select();
            document.execCommand('copy');
            // document.body.removeChild(ta);
            this.removeChild(ta);
            if (selected) {
                document.getSelection().removeAllRanges();
                document.getSelection().addRange(selected);
            }
            showMsg("code copied", "success")
        }catch(e){
            alert(e.message);
        }
        
        return false;
    });

    
    //deleteblog
    $("#deleteblogBttn").click(function () {
        var bttn = $(this);
        UIkit.modal.confirm('正在删除文章, 是否继续?').then(function () {
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

});
