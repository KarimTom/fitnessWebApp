var table = document.getElementById("my-Table");
var table_sug = document.getElementById("meal-suggestions");

//check if there are meal suggestions
if ((typeof(meal_sug) !== "undefined")){
    //meal suggestions exist -> append them to table of meal-suggestions
    for(let i = 0; i < meal_sug.length; i++){
        var newRow = table_sug.insertRow(0),
            meal = newRow.insertCell(0),
            protein = newRow.insertCell(1)
            carbs = newRow.insertCell(2)
            fat = newRow.insertCell(3)
            quantity = newRow.insertCell(4);

            meal.innerHTML = "<span class=table-text>"+meal_sug[i].name; +"</span>"
            protein.innerHTML = "<span class=table-text>"+meal_sug[i].Protein; +"</span>"
            carbs.innerHTML = "<span class=table-text>"+meal_sug[i].Carbs; +"</span>"
            fat.innerHTML = "<span class=table-text>"+meal_sug[i].Fat; +"</span>"
            quantity.innerHTML = "<span class=table-text>"+"100 gr";+"</span>"
                
            table_sug.appendChild(newRow);
    }
}

//check if last_meal is logged
if ((typeof(last_meal) != "undefined")){
    console.log(last_meal)
    last_meal_html = document.getElementById("last_meal_name_value");
    last_meal_html.innerHTML = last_meal.name;

    //check the status of meal (high in protein/high in carbs/ high in fat)
    status_meal = "";
    if(protein_flag != 0){
        status_meal += "High Protein ";
    }
    if(carb_flag != 0){
        status_meal += "High Carbs ";
    }
    if(fat_flag != 0){
        status_meal += "High Fat";
    }
    last_meal_status = document.getElementById("last_meal_status_value");
    last_meal_status.innerHTML = "";
    last_meal_status.innerHTML = status_meal;

    console.log(protein_flag);
    console.log(carb_flag);
    console.log(fat_flag);
}

//append all the meals taken to the table of meals
for(let i = 0; i < meals_taken.length; i++){
    var newRow = table.insertRow(table.length),
        meal = newRow.insertCell(0),
        protein = newRow.insertCell(1)
        carbs = newRow.insertCell(2)
        fat = newRow.insertCell(3)
        quantity = newRow.insertCell(4);

    meal.innerHTML = "<span class=table-text>"+meals_taken[i][0].name;+"</span>"
    protein.innerHTML = "<span class=table-text>"+meals_taken[i][1].protein;+"</span>"
    carbs.innerHTML = "<span class=table-text>"+meals_taken[i][2].carbs;+"</span>"
    fat.innerHTML = "<span class=table-text>"+meals_taken[i][3].fat;+"</span>"

    table.appendChild(newRow);
}


