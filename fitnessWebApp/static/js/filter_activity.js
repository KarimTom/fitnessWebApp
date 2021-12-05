$("#id_activity_category").change(function () {
    $.ajax({                       
        url: 'filter_activities/',
        data:{
            name: $('#id_activity_category').val(),
        },
       success: function (data) {  
          console.log(data);
          var list = document.getElementById("id_Intensity_estimator");
          console.log(list);
          list.innerHTML = "";  
          let html_data = '<option value="">---------</option>';
          data.forEach(function (activity) {
             html_data +=`<option value = "${activity.api_description}"> ${activity.api_description} </option>`
          });
          list.innerHTML = html_data; 
       }
   });
});