
$(document).ready(function() {
    // Navbar
    showLanguagesWhenClick();
    showLanguagesWhenClickSidebar();
    changeLanguageWhenClick();
});


function showLanguagesWhenClick(){
    // Show languages when clicking on languages the button
    $("#show-languages").on("click", function(){
        $("#main-nav .group").each(function(){
            $(this).toggleClass('hidden');
        });
    });

    // Hide languages when clicking on the back arrow
    $("#show-languages-back").on("click", function(){
        $("#main-nav .group").each(function(){
            $(this).toggleClass('hidden');
        });
    });
}

function showLanguagesWhenClickSidebar(){
    // Show languages when clicking on languages the button
    $("#show-languages-sidebar").on("click", function(){
        $("#sidebar li").each(function(){
            $(this).toggleClass('hidden');
        });
    });

    // Go back when clicking on the back arrow
    $("#show-languages-sidebar-back").on("click", function(){
        $("#sidebar li").each(function(){
            $(this).toggleClass('hidden');
        });
    });
}

function changeLanguageWhenClick(){
    $('.language-option').on("click", function() {
        console.log($(this).val());
        var selectedLanguage = $(this).attr('value');
        $.ajax({
            url: '/set_language/' + selectedLanguage,
            type: 'POST',
            success: function(response) {
                if (response.status.includes("Language changed")) {
                    location.reload();
                } else {
                    alert(response.status);
                }
            },
            error: function() {
                alert('Error changing language');
            }
        });
    });
}

function toggleHidden(element){
    $(element).toggleClass('hidden');
}