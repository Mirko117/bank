$(document).ready(function() {
    $("#sidebar a").on("click", function(e) {
        e.preventDefault();
        $("#sidebar a").removeClass("selected");
        this.classList.add("selected");

        var url = this.href;
        
    });
});
