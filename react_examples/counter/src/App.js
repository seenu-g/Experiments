import ReactDOM from 'react-dom'
//import React from 'react';
import React, { useState } from 'react';

/*
function Button() {
  const [counter, setCounter] = useState(1);
	return <button onClick={() => setCounter(counter+1)}>{counter}</button>;

	// return <button>Stateless Button!</button>;
}

ReactDOM.render(
  <Button />, 
  document.getElementById('root'),
); 

export default Button;

*/

function Button(props) {
	return (
  	<button onClick={props.onClickFunction}>
      "Click To Increment!"
    </button>
  );
}

/* data can now flow from the parent to the child. parent is App and child is Presentation */
/* make use of props object to send date from parent to child */
function Presentation(props) {
	return (
  	<li>{props.message}</li>
  );
}

function Employee(props){

  return ( 
  <div style={{border:"3px solid red"}}>
    <p>Employee ID : <b>{props.data.Id}</b></p>
    <p>Employee Name : <b>{props.data.Name}</b></p>
    <p>Employee Location : <b>{props.data.Location}</b></p>
    <p>Employee Salary : <b>{props.data.Salary}</b></p>
  </div>
  );
}
function DislayEmployees(props) {
  
  const list = props.employeeList;
  const listElements = list.map((emp) =><Employee key={emp.Id}  data={emp} ></Employee> );
  
  return (listElements);
  }

const employees = [
  {Id:101,Name:'Abhinav',Location:'Bangalore',Salary:12345},
  {Id:102,Name:'Abhishek',Location:'Chennai',Salary:23456},
  {Id:103,Name:'Ajay',Location:'Bangalore',Salary:34567} 
  ];

/* To make the counter state accessible to both components, we need to create a parent component. */
function App() {
	const [counter1, addCounter] = useState(0);
  const incrementCounter = () => addCounter(counter1+1);
 
  const [counter2, reduceCounter] = useState(100);
  const decrementCounter = () => reduceCounter(counter2-1);

	return (
    <div>
      <Button onClickFunction={incrementCounter}  />
      <Presentation message={counter1}/>

     <Button onClickFunction={decrementCounter}  />
     <Presentation message={counter2}/>

     <DislayEmployees employeeList ={employees} />

   </div> 
  );
}

ReactDOM.render(
  <App />, 
  document.getElementById('root'),
);

export default App;


  


