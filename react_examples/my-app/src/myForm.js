import React from 'react';
import { useState } from 'react';
function MyForm() {
  const [person_name, setName] = useState("");
  const [mobile, setMobile] = useState("");
  const [textarea, setTextarea] = useState(
    "The content of a textarea goes in the value attribute"
  );

  const [inputs, setInputs] = useState({});

  const handleChange = (event) => {
    const name = event.target.name;
    const value = event.target.value;
    if (event.target.name ==="input_1"){
      setName(event.target.value)
      setInputs(values => ({...values, [name]: value}))
    }
     if (event.target.name ==="your_mobile"){
      setMobile(event.target.value)
      setInputs(values => ({...values, [name]: value}))
    }
    if (event.target.name ==="textarea_1"){
      setTextarea(event.target.value)
      setInputs(values => ({...values, [name]: value}))
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault();
    console.log(person_name)
    console.log(mobile)
    console.log(textarea)
    console.log(inputs);

  }

  return (
    <form onSubmit={handleSubmit}>
      <label>Enter your name: </label>
        <input
          type="text" 
          name= "input_1"
          value={person_name}
         // onChange={(e) => setName(e.target.value)}
         onChange={handleChange}
        />
      <br></br>

      <select name = "your_mobile" value={mobile} onChange={handleChange}>
        <option value="Apple">Apple</option>
        <option value="Samsung">Samsung</option>
        <option value="Nokia">Nokia</option>
      </select>
      <br></br>

      <textarea  name= "textarea_1" value={textarea} onChange={handleChange} />
      <br></br>

      <input type="submit" />
    </form>
  )
}
export default MyForm ; 
/* const root = ReactDOM.createRoot(document.getElementById('root'));*/