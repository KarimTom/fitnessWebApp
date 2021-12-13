$(function() {
    $("#id_api_description").autocomplete({
        source: 'autocomplete/',        //triggers autocomplete function in views.py to return a list of activities 
                                        //in which the user's input words exist in the activities 
                                        //(example: user's input - ru  -> autocomplete: run, running, runner, etc..)
        
        minLength: 2                    //length of user's input word that makes the function execute                    
    });
});
