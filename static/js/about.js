/**
 * created by larsson on 9.25 2018
 * data storage in html elements was not comfort HTML5 standard
 */

$(document).ready(function () {

    //online days
    var onlineStart = "2018-9-24 13:56";
    var startDate = Date.parse(onlineStart.replace('/-/g', '/'));
    var now = new Date();
    var diffDate = (now - startDate);//+1*24*60*60*1000;  
    var diffDaysStr = diffDate / (1 * 24 * 60 * 60 * 1000);
    var onlinedays = $("span[onlinedays]");
    $(onlinedays).text(diffDaysStr.toFixed(0));
});


