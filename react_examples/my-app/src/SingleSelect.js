import React, { useState } from "react";
import { RadioButton } from "./RadioButton";

export default function SingleSelect(props) {
  const [paymentMethod, setPaymentMethod] = useState("COD");

  const radioChangeHandler = (e) => {
    setPaymentMethod(e.target.value);
  };
  
  var items = null 
  if (props.list == null){
     items = [
      {id: 1, value: 'QuickPay', label : "quick Payment"},
      {id: 2, value: 'COD', label : "Cash On Delivery"},
    ];
  }
  else items = props.list;

  return (
    <>
     <h3>{props.name}</h3>
     <div className="SingleSelect">
      <div className="radio-btn-container" >
      <ul>{items.map((item) => 
       <RadioButton
                  changed={radioChangeHandler}
                  id= {item.id}
                  isSelected={paymentMethod === item.value}
                  label={item.label}
                  value= {item.value}
                />)}
      </ul>
      </div>
      {paymentMethod === "QuickPay" && (
        <input
          style={{ marginTop: "10px" }}
          type="text"
          placeholder="Enter transaction id"
        />
      )}

      <h4 style={{ marginTop: "25px" }}>
        The selected radio button value is = {paymentMethod}
      </h4>
      
    </div>
  </>
  );
}
