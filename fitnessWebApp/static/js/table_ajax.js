$(document).on('submit', '#meal_input', function(e){
    console.log("enter was pressed");
    e.preventDefault();

    $.ajax({
        type:'POST',
        url: 'create/',
        data:{
            name: $('#meal-input').val(),
            'csrfmiddlewaretoken': '{{ csrf_token }}',
        },
        success: function(response){
            console.log(response.last_meal);

            last_meal_html = document.getElementById("last_meal_name_value");
            console.log(last_meal_html);
            last_meal_html.innerHTML = "";
            last_meal_html.innerHTML = response.last_meal.name;

            var table = document.getElementById("my-Table");

            var newRow = table.insertRow(table.length),
            meal = newRow.insertCell(0),
            protein = newRow.insertCell(1),
            carbs = newRow.insertCell(2),
            fat = newRow.insertCell(3);

            meal.innerHTML = "<span class=table-text>"+response.last_meal.name +"</span>";
            protein.innerHTML = "<span class=table-text>"+response.last_meal.protein +"</span>";
            carbs.innerHTML = "<span class=table-text>"+response.last_meal.carbs +"</span>";
            fat.innerHTML = "<span class=table-text>"+response.last_meal.fat +"</span>";

            table.appendChild(newRow);

            status_meal = "";
            if(response.protein_flag != 0){
                status_meal += "High Protein ";
            }
            if(response.carb_flag != 0){
                status_meal += "High Carbs ";
            }
            if(response.fat_flag != 0){
                status_meal += "High Fat";
            }
            last_meal_status = document.getElementById("last_meal_status_value");
            last_meal_status.innerHTML = status_meal;

            if ((typeof(response.food_sug) !== "undefined")){
                var table = document.getElementById("meal-suggestions");
            
                for(let i = table.rows.length - 1; i > 0; i--){
                    table.deleteRow(i);
                }

                for(let i = 0; i < response.food_sug.length; i++){
                    var newRow = table.insertRow(0),
                        meal = newRow.insertCell(0),
                        protein = newRow.insertCell(1)
                        carbs = newRow.insertCell(2)
                        fat = newRow.insertCell(3)
                        quantity = newRow.insertCell(4);
                    console.log(response.food_sug[i]);
                    meal.innerHTML = "<span class=table-text>"+response.food_sug[i].name; +"</span>"
                    protein.innerHTML = "<span class=table-text>"+response.food_sug[i].Protein; +"</span>"
                    carbs.innerHTML = "<span class=table-text>"+response.food_sug[i].Carbs; +"</span>"
                    fat.innerHTML = "<span class=table-text>"+response.food_sug[i].Fat; +"</span>"
                
                    table.appendChild(newRow);
                }
            }
        }
    });
});