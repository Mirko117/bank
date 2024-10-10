$(document).ready(function(){
    registrationAjax();
    loginAjax();
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
                    alert(response.status);
                    window.location.href = '/auth/login';
                } else {
                    alert(response.status);
                }
            },
            error: function(response){
                alert(response.responseJSON.status);
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
                    alert(response.status);
                    window.location.href = '/dashboard';
                } else {
                    alert(response.status);
                }
            },
            error: function(response){
                alert(response.responseJSON.status);
            }
        });
    });
}