$(document).ready(function(){
    registrationAjax();
    loginAjax();
    loginAutofillUsername();
});

function registrationAjax(){
    $('#register .wrapper form').on('submit', function(e){
        e.preventDefault();

        var formData = $(this).serialize();

        $.ajax({
            type: 'POST',
            url: '/auth/register',
            data: formData,
            success: function(response){
                if(response.status.includes("User created")){
                    authDialog(response.status, response.title, response.redirect);
                } else {
                    authDialog(response.status, response.title);
                }
            },
            error: function(response){
                authDialog(response.responseJSON.status, response.responseJSON.title);
            }
        });
    });
}


function loginAjax(){
    $('#login .wrapper form').on('submit', function(e){
        e.preventDefault();

        var formData = $(this).serialize();

        $.ajax({
            type: 'POST',
            url: '/auth/login',
            data: formData,
            success: function(response){
                if(response.status.includes("Logged in")){
                    authDialog(response.status, "Success", '/dashboard');
                } else {
                    authDialog(response.status, "Error");
                }
            },
            error: function(response){
                authDialog(response.responseJSON.status, "Error");
            }
        });
    });
}

function loginAutofillUsername(){
    const urlParams = new URLSearchParams(window.location.search);
    const username = urlParams.get('username');
    if(username){
        $('#login .wrapper form input[name="username"]').val(username);
    }
}


function authDialog(text, title, redirect=false){
    $("<div>" + text + "</div>").dialog({
        title: title,
        modal: true,
        resizable: false,
        draggable: false,
        position: { my: "top+100", at: "top", of: window },
        buttons: {
            Ok: function(){
                $(this).dialog('close');
                return true;
            }
        },
        close: function(){
            if(redirect){
                window.location.href = redirect;
            }
        }
    });
}