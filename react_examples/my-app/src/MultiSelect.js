import React, { useState } from "react";
import { CheckBox } from "./CheckBox";

export default function MultiSelect(props) {
  const [eduLevel, seteduLevel] = useState(null);

  const optionChangeHandler = (e) => {
    seteduLevel(e.target.value);
  };

  var items = null 
  if (props.list == null){
     items = [
      {id: 1, value: 'Bachelors', label : "Bachelors"},
      {id: 2, value: 'Masters', label : "Masters"},
    ];
  }
  else items = props.list;
  
  return (
    <>
    <h3>{props.name}</h3>
    <div className="MultiSelect">
      { props.title}
      <div className="check-box-container">
      <ul>{items.map((item) => 
          <CheckBox
                id={item.id}
                label={item.label}
                value= {item.value}
                isChecked={eduLevel === item.value}
                changed = {optionChangeHandler}
                />
          )}
      </ul>
      </div>

      {eduLevel === "Others" && (
        <input
          style={{ marginTop: "10px" }}
          type="text"
          placeholder="Enter education Level"
        />
      )}

      <h3 style={{ marginTop: "25px" }}>
        The selected checkbox value is = {eduLevel}
      </h3>
      
    </div>
    </>
  );
}
