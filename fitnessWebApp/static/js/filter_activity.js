$("#id_activity_category").change(function () {
    $.ajax({                       
        url: 'filter_activities/',      //function in views.py
        data:{
            name: $('#id_activity_category').val(),     //what activity category user has chosen from the drop down list
        },
       success: function (data) {  
          var list = document.getElementById("id_Intensity_estimator");         //grab the intensity estimator input field in the form
          list.innerHTML = "";  
          
          //filter the relevant activities for the category the user has chosen
          let html_data = '<option value="">---------</option>';        
          data.forEach(function (activity) {
             html_data +=`<option value = "${activity.api_description}"> ${activity.api_description} </option>`
          });
          list.innerHTML = html_data; 
       }
   });
});